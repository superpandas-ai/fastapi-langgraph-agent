from langchain_openai import ChatOpenAI
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    Literal,
    Optional,
)
from langgraph.graph import StateGraph, END
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.schemas.chat import ChatResponse
from app.schemas.superpandas import GraphState
from app.core.langgraph.superpandas.codeparser import CodeBlobOutputParser
from smolagents import LocalPythonExecutor, DockerExecutor
from app.core.prompts.superpandas import code_generation_prompt_template, reflection_prompt_template, format_response_prompt_template

from app.core.metrics import llm_inference_duration_seconds
from app.core.config import (
    Environment,
    settings,
)
from app.core.logging import logger
from psycopg_pool import AsyncConnectionPool
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import StateSnapshot
from asgiref.sync import sync_to_async
from langfuse.callback import CallbackHandler

from app.utils import (
    dump_messages,
    prepare_messages,
)
from openai import OpenAIError
from langchain_core.messages import (
    BaseMessage,
    ToolMessage,
    convert_to_openai_messages,
)
from app.schemas import Message
from pathlib import Path
import sqlite3

base_path = Path("app/core/langgraph/superpandas/")


def get_sql_schema(platform: str) -> tuple[sqlite3.Connection, str]:
    db_path = Path(base_path, 'databases', platform+'.db')
    sql_path = Path(base_path, 'databases', platform+'.sql')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    with open(sql_path, 'r') as f:
        sql_schema = f.read()
        sql_schema = ''.join(sql_schema)
    return conn, sql_schema


class SuperpandasAgent:
    """Manages the LangGraph Agent/workflow and interactions with the LLM.

    This class handles the creation and management of the LangGraph workflow,
    including LLM interactions, database connections, and response processing.
    """

    def __init__(self, platform: Literal["fic", "sevdesk", "hr"]):
        """Initialize the LangGraph Agent with necessary components."""
        # Use environment-specific LLM model
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.DEFAULT_LLM_TEMPERATURE,
            api_key=settings.LLM_API_KEY,
            max_tokens=settings.MAX_TOKENS,
            **self._get_model_kwargs(),
        )  # .bind_tools(tools)
        # self.tools_by_name = {tool.name: tool for tool in tools}
        self._connection_pool: Optional[AsyncConnectionPool] = None
        self._graph: Optional[CompiledStateGraph] = None
        self.conn, self.sql_schema = get_sql_schema(platform)

        # Create the prompt template for reflection
        reflection_prompt = PromptTemplate.from_template(
            reflection_prompt_template
        )

        # Create the prompt template for formatting the response
        format_prompt = PromptTemplate.from_template(
            format_response_prompt_template
        )

        self.code_gen_chain = self.llm | CodeBlobOutputParser()
        self.reflection_chain = reflection_prompt | self.llm | StrOutputParser()
        self.format_chain = format_prompt | self.llm | StrOutputParser()

        logger.info("llm_initialized", model=settings.LLM_MODEL,
                    environment=settings.ENVIRONMENT.value)

    def _get_model_kwargs(self) -> Dict[str, Any]:
        """Get environment-specific model kwargs.

        Returns:
            Dict[str, Any]: Additional model arguments based on environment
        """
        model_kwargs = {}

        # Development - we can use lower speeds for cost savings
        if settings.ENVIRONMENT == Environment.DEVELOPMENT:
            model_kwargs["top_p"] = 0.8

        # Production - use higher quality settings
        elif settings.ENVIRONMENT == Environment.PRODUCTION:
            model_kwargs["top_p"] = 0.95
            model_kwargs["presence_penalty"] = 0.1
            model_kwargs["frequency_penalty"] = 0.1

        return model_kwargs

    async def _get_connection_pool(self) -> AsyncConnectionPool:
        """Get a PostgreSQL connection pool using environment-specific settings.

        Returns:
            AsyncConnectionPool: A connection pool for PostgreSQL database.
        """
        if self._connection_pool is None:
            try:
                # Configure pool size based on environment
                max_size = settings.POSTGRES_POOL_SIZE

                self._connection_pool = AsyncConnectionPool(
                    settings.POSTGRES_URL,
                    open=False,
                    max_size=max_size,
                    kwargs={
                        "autocommit": True,
                        "connect_timeout": 5,
                        "prepare_threshold": None,
                    },
                )
                await self._connection_pool.open()
                logger.info("connection_pool_created", max_size=max_size,
                            environment=settings.ENVIRONMENT.value)
            except Exception as e:
                logger.error("connection_pool_creation_failed", error=str(
                    e), environment=settings.ENVIRONMENT.value)
                # In production, we might want to degrade gracefully
                if settings.ENVIRONMENT == Environment.PRODUCTION:
                    logger.warning("continuing_without_connection_pool",
                                   environment=settings.ENVIRONMENT.value)
                    return None
                raise e
        return self._connection_pool

    async def _generate_code(self, state: GraphState) -> dict:
        """Process the chat state and generate a response.

        Args:
            state (GraphState): The current state of the conversation.

        Returns:
            dict: Updated state with new messages.
        """

        messages = prepare_messages(
            state.messages, self.llm, code_generation_prompt_template, self.sql_schema)

        llm_calls_num = 0

        # Configure retry attempts based on environment
        max_retries = settings.MAX_LLM_CALL_RETRIES

        for attempt in range(max_retries):
            try:
                with llm_inference_duration_seconds.labels(model=self.llm.model_name).time():
                    generated_code = await self.code_gen_chain.ainvoke(dump_messages(messages))
                    generated_state = {"generated_code": generated_code}
                logger.info(
                    "code_generated",
                    session_id=state.session_id,
                    llm_calls_num=llm_calls_num + 1,
                    model=settings.LLM_MODEL,
                    environment=settings.ENVIRONMENT.value,
                )
                return generated_state
            except OpenAIError as e:
                logger.error(
                    "code_generation_failed",
                    llm_calls_num=llm_calls_num,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                    environment=settings.ENVIRONMENT.value,
                )
                llm_calls_num += 1

                # In production, we might want to fall back to a more reliable model
                if settings.ENVIRONMENT == Environment.PRODUCTION and attempt == max_retries - 2:
                    fallback_model = "gpt-4o"
                    logger.warning(
                        "using_fallback_model", model=fallback_model, environment=settings.ENVIRONMENT.value
                    )
                    self.llm.model_name = fallback_model

                continue

        raise Exception(
            f"Failed to generate code after {max_retries} attempts. Error: {e}")

    # Node 2: Execute code
    def _execute_code(self, state: GraphState) -> GraphState:
        generated_code = state.generated_code
        conn = self.conn

        local_env = {'conn': conn}

        if generated_code == "NO_DATA_FOUND":
            state.error = "NO_DATA_FOUND"
            return state

        try:
            # TODO: Use smolagents to execute the code
            exec(generated_code, local_env)
            # print("[DEBUG] Code executed. Local keys:", local_env.keys())

            if "result" in local_env:
                state.result = local_env["result"]
                # print("[DEBUG] Extracted result:", state["result"])
            else:
                state.error = "Dataframe not set in the generated code."
                # print("[ERROR] 'result' not found after code execution.")

            if "fig" in local_env:
                state.fig = local_env["fig"]

        except Exception as e:
            state.error = str(e)
            state.messages.append(
                {"role": "assistant",
                    "content": f"Error executing code: {str(e)}"}
            )

        return state

    # Node 3: Reflect on errors
    def _reflect(self, state: GraphState) -> GraphState:
        """Reflect on errors and provide insights on how to fix them"""
        # Get the error and code
        error = state.error
        code = state.generated_code

        # Generate reflection
        reflection = self.reflection_chain.invoke(
            {"error": error, "code": code})

        # Add the reflection to the messages
        state.messages.append(
            {"role": "assistant", "content": f"Reflection on the error: {reflection}"}
        )

        # Clear the error
        state.error = ""

        return state

    # Node 4: Format response
    def _format_response(self, state: GraphState) -> GraphState:
        """Format the response into proper text form"""
        # Get the response and current query
        result = state.result
        generated_code = state.generated_code
        current_query = state.messages[0].content

        # Format the response
        formatted_response = self.format_chain.invoke(
            {
                "result": result,
                "current_query": current_query,
                "generated_code": generated_code,
                "language": 'english',
            }
        )
        logger.debug(f"Generated Code: {generated_code}")
        logger.debug(f"Formatted Response: {formatted_response}")

        # Update the state
        state.messages.append(
            {"role": "assistant", "content": formatted_response}
        )

        return state

    # Node 5: Check for errors
    def _check_execution_errors(self, state: GraphState) -> str:
        """Check if there are any errors in the execution"""
        # If there's an error, we need to fix it
        if state.error:
            # If we've reached the maximum number of iterations, end
            if state.iterations >= settings.MAX_LLM_CALL_RETRIES or state.error == "NO_DATA_FOUND":
                return "end"
            else:
                # Otherwise, reflect on the error and try to fix it
                return "reflect"

        # If there's no error, format the response
        return "format"

    # Node 5: Check for errors
    def _check_codegen_errors(self, state: GraphState) -> str:
        """Check if there are any errors in the code generation"""
        # If there's an error, we need to fix it
        if state.error:
            # If we've reached the maximum number of iterations, end
            if state.iterations >= settings.MAX_LLM_CALL_RETRIES:
                return "end"
            else:
                # Otherwise, reflect on the error and try to fix it
                return "reflect"

        # If there's no error, execute the code
        return "execute_code"
    # Define our tool node

    async def _tool_call(self, state: GraphState) -> GraphState:
        """Process tool calls from the last message.

        Args:
            state: The current agent state containing messages and tool calls.

        Returns:
            Dict with updated messages containing tool responses.
        """
        outputs = []
        for tool_call in state.messages[-1].tool_calls:
            tool_result = await self.tools_by_name[tool_call["name"]].ainvoke(tool_call["args"])
            outputs.append(
                ToolMessage(
                    content=tool_result,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

    def _should_continue(self, state: GraphState) -> Literal["end", "continue"]:
        """Determine if the agent should continue or end based on the last message.

        Args:
            state: The current agent state containing messages.

        Returns:
            Literal["end", "continue"]: "end" if there are no tool calls, "continue" otherwise.
        """
        messages = state.messages
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not last_message.tool_calls:
            return "end"
        # Otherwise if there is, we continue
        else:
            return "continue"

    async def create_graph(self) -> Optional[CompiledStateGraph]:
        """Create and configure the LangGraph workflow.

        Returns:
            Optional[CompiledStateGraph]: The configured LangGraph instance or None if init fails
        """
        if self._graph is None:
            try:
                graph_builder = StateGraph(GraphState)
                graph_builder.add_node("generate_code", self._generate_code)
                graph_builder.add_node("execute_code", self._execute_code)
                graph_builder.add_node("reflect", self._reflect)
                graph_builder.add_node("format", self._format_response)

                graph_builder.add_edge("generate_code", "execute_code")
                graph_builder.add_conditional_edges(
                    "execute_code",
                    self._check_execution_errors,
                    {"reflect": "reflect", "format": "format", "end": END},
                )
                graph_builder.set_entry_point("generate_code")
                graph_builder.set_finish_point("format")

                # Get connection pool (may be None in production if DB unavailable)
                connection_pool = await self._get_connection_pool()
                if connection_pool:
                    checkpointer = AsyncPostgresSaver(connection_pool)
                    await checkpointer.setup()
                else:
                    # In production, proceed without checkpointer if needed
                    checkpointer = None
                    if settings.ENVIRONMENT != Environment.PRODUCTION:
                        raise Exception(
                            "Connection pool initialization failed")

                self._graph = graph_builder.compile(
                    checkpointer=checkpointer, name=f"{settings.PROJECT_NAME} Agent ({settings.ENVIRONMENT.value})"
                )

                logger.info(
                    "graph_created",
                    graph_name=f"{settings.PROJECT_NAME} Agent",
                    environment=settings.ENVIRONMENT.value,
                    has_checkpointer=checkpointer is not None,
                )
            except Exception as e:
                logger.error("graph_creation_failed", error=str(
                    e), environment=settings.ENVIRONMENT.value)
                # In production, we don't want to crash the app
                if settings.ENVIRONMENT == Environment.PRODUCTION:
                    logger.warning("continuing_without_graph")
                    return None
                raise e

        return self._graph

    async def get_response(
        self,
        messages: list[Message],
        session_id: str,
        user_id: Optional[str] = None,
    ) -> ChatResponse:
        """Get a response from the LLM.

        Args:
            state (GraphState): The state of the conversation.
            user_id (Optional[str]): The user ID for Langfuse tracking.

        Returns:
            list[dict]: The response from the LLM.
        """

        if self._graph is None:
            self._graph = await self.create_graph()
        config = {
            "configurable": {"thread_id": session_id},
            "callbacks": [
                CallbackHandler(
                    environment=settings.ENVIRONMENT.value,
                    debug=False,
                    user_id=user_id,
                    session_id=session_id,
                )
            ],
        }

        state = GraphState(messages=messages,
                           session_id=session_id,
                           generated_code="",
                           error="",
                           iterations=0,
                           result="",
                           fig=None)
        try:
            response = await self._graph.ainvoke(
                state.model_dump(),
                config
            )

            return ChatResponse(messages=self.__process_messages(response["messages"]),
                                generated_code=response.get("generated_code"),
                                fig=response.get("fig"))
        except Exception as e:
            logger.error(f"Error getting response: {str(e)}")
            raise e

    async def get_stream_response(
        self, messages: list[Message], session_id: str, user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Get a stream response from the LLM.

        Args:
            state (GraphState): The state of the conversation.
            user_id (Optional[str]): The user ID for the conversation.

        Yields:
            str: Tokens of the LLM response.
        """

        config = {
            "configurable": {"thread_id": session_id},
            "callbacks": [
                CallbackHandler(
                    environment=settings.ENVIRONMENT.value, debug=False, user_id=user_id, session_id=session_id
                )
            ],
        }
        if self._graph is None:
            self._graph = await self.create_graph()

        state = GraphState(messages=messages,
                           session_id=session_id,
                           generated_code="",
                           error="",
                           iterations=0,
                           result="",
                           fig=None)

        try:
            async for token, _ in self._graph.astream(
                state.model_dump(),
                config,
                stream_mode="messages",
            ):
                try:
                    yield token.content
                except Exception as token_error:
                    logger.error("Error processing token", error=str(
                        token_error), session_id=session_id)
                    # Continue with next token even if current one fails
                    continue
        except Exception as stream_error:
            logger.error("Error in stream processing", error=str(
                stream_error), session_id=session_id)
            raise stream_error

    async def get_chat_history(self, session_id: str) -> list[Message]:
        """Get the chat history for a given thread ID.

        Args:
            session_id (str): The session ID for the conversation.

        Returns:
            list[Message]: The chat history.
        """
        if self._graph is None:
            self._graph = await self.create_graph()

        state: StateSnapshot = await sync_to_async(self._graph.get_state)(
            config={"configurable": {"thread_id": session_id}}
        )
        return self.__process_messages(state.values["messages"]) if state.values else []

    def __process_messages(self, messages: list[BaseMessage]) -> list[Message]:
        openai_style_messages = convert_to_openai_messages(messages)
        # keep just assistant and user messages
        return [
            Message(**message)
            for message in openai_style_messages
            if message["role"] in ["assistant", "user"] and message["content"]
        ]

    async def clear_chat_history(self, session_id: str) -> None:
        """Clear all chat history for a given thread ID.

        Args:
            session_id: The ID of the session to clear history for.

        Raises:
            Exception: If there's an error clearing the chat history.
        """
        try:
            # Make sure the pool is initialized in the current event loop
            conn_pool = await self._get_connection_pool()

            # Use a new connection for this specific operation
            async with conn_pool.connection() as conn:
                for table in settings.CHECKPOINT_TABLES:
                    try:
                        await conn.execute(f"DELETE FROM {table} WHERE thread_id = %s", (session_id,))
                        logger.info(
                            f"Cleared {table} for session {session_id}")
                    except Exception as e:
                        logger.error(f"Error clearing {table}", error=str(e))
                        raise

        except Exception as e:
            logger.error("Failed to clear chat history", error=str(e))
            raise
