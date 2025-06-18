import sqlite3
from matplotlib import pyplot as plt
import pandas as pd
import streamlit as st
from typing import Dict, List, Any, Annotated
from typing_extensions import TypedDict
import streamlit as st
import os
from langgraph.graph import StateGraph, END
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
)
from langchain_core.output_parsers import StrOutputParser
from .codeparser import CodeBlobOutputParser
from smolagents import LocalPythonExecutor, DockerExecutor
from .superpandas_prompts import sql_code_generation_prompt, sql_reflection_prompt, sql_format_response_prompt
from langgraph.graph.message import add_messages
from typing import Annotated, Any
from translations import get_translation
import uuid
from datetime import datetime
from utils import (
    get_sql_schema,
    get_sample_questions,
    get_context_messages,
    store_feedback,
    create_conversation_zip
)
from config import CONFIG

os.environ["LANGSMITH_API_KEY"] = st.secrets["api_keys"][CONFIG.get('api_key')]
os.environ["LANGSMITH_PROJECT"] = CONFIG.get('langsmith_project')

# Define the state for our graph


class AgentState(TypedDict):
    messages: Annotated[List[Dict[str, str]], add_messages]
    current_query: Annotated[str, "last"]
    datasource: sqlite3.Connection
    generated_code: str
    error: str
    iterations: int
    formatted_response: str
    result: Any
    fig: Any


# Define the maximum number of iterations
MAX_ITERATIONS = 3


def create_langgraph_agent():
    """
    Create a LangGraph agent for data analysis

    Returns:
        StateGraph: The compiled LangGraph agent
    """

    # Create the prompt template for code generation
    code_gen_prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    # Create the prompt template for reflection
    reflection_prompt = PromptTemplate.from_template(
        sql_reflection_prompt
    )

    # Create the prompt template for formatting the response
    format_prompt = PromptTemplate.from_template(
        sql_format_response_prompt
    )

    # Create the model chains
    code_gen_chain = code_gen_prompt | st.session_state.llm_70b | CodeBlobOutputParser()
    reflection_chain = reflection_prompt | st.session_state.llm_70b | StrOutputParser()
    format_chain = format_prompt | st.session_state.llm_70b | StrOutputParser()

    # Define the nodes for our graph
    # Node 1: Generate code
    def generate_code(state: AgentState) -> AgentState:
        """Generate code based on the current query and dataframe schema"""
        # Get the current query and dataframe schema
        # current_query = state["current_query"]
        # datasource_schema = state["datasource_schema"]

        # Get the messages
        messages = state["messages"]

        # Generate the code
        try:
            generated_code = code_gen_chain.invoke(
                {
                    "messages": messages,
                }
            )
        except ValueError as e:
            generated_code = ""
            state["error"] = str(e)
            state["messages"].append(
                {"role": "assistant",
                    "content": f"Error generating code: {str(e)}"}
            )

        # Update the state
        state["generated_code"] = generated_code
        state["iterations"] += 1

        return state

    # Node 2: Execute code
    def execute_code(state: AgentState) -> AgentState:
        generated_code = state["generated_code"]
        conn = state["datasource"]

        local_env = {'conn': conn}

        if generated_code == "NO_DATA_FOUND":
            state["error"] = "NO_DATA_FOUND"
            return state

        try:
            # TODO: Use smolagents to execute the code
            exec(generated_code, local_env)
            # print("[DEBUG] Code executed. Local keys:", local_env.keys())

            if "result" in local_env:
                state["result"] = local_env["result"]
                # print("[DEBUG] Extracted result:", state["result"])
            else:
                state["error"] = "Dataframe not set in the generated code."
                # print("[ERROR] 'result' not found after code execution.")

            if "fig" in local_env:
                state["fig"] = local_env["fig"]

        except Exception as e:
            state["error"] = str(e)
            state["messages"].append(
                {"role": "assistant",
                    "content": f"Error executing code: {str(e)}"}
            )

        return state

    # Node 3: Reflect on errors
    def reflect(state: AgentState) -> AgentState:
        """Reflect on errors and provide insights on how to fix them"""
        # Get the error and code
        error = state["error"]
        code = state["generated_code"]

        # Generate reflection
        reflection = reflection_chain.invoke({"error": error, "code": code})

        # Add the reflection to the messages
        state["messages"].append(
            {"role": "assistant", "content": f"Reflection on the error: {reflection}"}
        )

        # Clear the error
        state["error"] = ""

        return state

    # Node 4: Format response
    def format_response(state: AgentState) -> AgentState:
        """Format the response into proper text form"""
        # Get the response and current query
        result = state["result"]
        generated_code = state["generated_code"]

        # Format the response
        formatted_response = format_chain.invoke(
            {
                "result": result,
                "current_query": state["current_query"],
                "generated_code": generated_code,
                "language": st.session_state.language.lower(),
            }
        )
        print(f"DEBUG - Generated Code: {generated_code}")

        # Update the state
        state["formatted_response"] = formatted_response

        return state

    # Node 5: Check for errors
    def check_execution_errors(state: AgentState) -> str:
        """Check if there are any errors in the execution"""
        # If there's an error, we need to fix it
        if state["error"]:
            # If we've reached the maximum number of iterations, end
            if state["iterations"] >= MAX_ITERATIONS or state["error"] == "NO_DATA_FOUND":
                return "end"
            else:
                # Otherwise, reflect on the error and try to fix it
                return "reflect"

        # If there's no error, format the response
        return "format"

    # Node 5: Check for errors
    def check_codegen_errors(state: AgentState) -> str:
        """Check if there are any errors in the code generation"""
        # If there's an error, we need to fix it
        if state["error"]:
            # If we've reached the maximum number of iterations, end
            if state["iterations"] >= MAX_ITERATIONS:
                return "end"
            else:
                # Otherwise, reflect on the error and try to fix it
                return "reflect"

        # If there's no error, execute the code
        return "execute_code"

    # Create the graph
    workflow = StateGraph(AgentState)

    # Add the nodes
    workflow.add_node("generate_code", generate_code)
    workflow.add_node("execute_code", execute_code)
    workflow.add_node("reflect", reflect)
    workflow.add_node("format", format_response)

    # Add the edges
    workflow.add_edge("generate_code", "execute_code")
    workflow.add_conditional_edges(
        "execute_code",
        check_execution_errors,
        {"reflect": "reflect", "format": "format", "end": END},
    )
    workflow.add_conditional_edges(
        "generate_code",
        check_codegen_errors,
        {"reflect": "reflect", "execute_code": "execute_code", "end": END},
    )
    workflow.add_edge("reflect", "generate_code")
    workflow.add_edge("format", END)

    # Set the entry point
    workflow.set_entry_point("generate_code")

    # Compile the graph
    agent = workflow.compile()

    return agent


def generate_and_execute(
    query: str, conn: sqlite3.Connection, sql_schema: str
) -> tuple[str, list]:
    """
    Generate and execute SQL code to answer the user's question using the provided SQLite connection with LangGraph

    Args:
        query (str): User's question
        conn (sqlite3.Connection): SQLite database connection
        sql_schema (sqlite3.Cursor): Cursor containing table schema information

    Returns:
        tuple[str, list]: Response and agent memory steps
    """

    # Create the LangGraph agent with SQL framework
    agent = create_langgraph_agent()

    messages = st.session_state.messages
    if messages[0]["role"] != "system":
        messages.insert(
            0,
            {
                "role": "system",
                "content": sql_code_generation_prompt.format(
                    datasource_schema=sql_schema,
                    current_query=query,
                ),
            },
        )

    # Initialize the state
    initial_state = AgentState(
        messages=messages,
        current_query=query,
        datasource=conn,
        error="",
        iterations=0,
        generated_code="",
        formatted_response="",
        result="",
        fig="",
    )

    try:
        final_state = agent.invoke(initial_state)
    except Exception as e:
        final_state = initial_state
        final_state["generated_code"] = ""
        final_state["error"] = str(e)

    generated_code = str(final_state.get("generated_code", ""))

    # Check if the code indicates no data is available
    if generated_code == "NO_DATA_FOUND":
        final_state["formatted_response"] = "Required information is not available in the given database."
    elif generated_code == "":
        final_state["formatted_response"] = "Error executing agent. We have logged the error and will fix it soon. Please try another question."

    # Return the formatted response
    return final_state["formatted_response"], final_state["generated_code"], final_state["result"], final_state["fig"]


def show_conversation_sidebar():
    """Show a feedback form in the sidebar for the current conversation"""
    st.sidebar.markdown("---")
    st.sidebar.subheader(get_translation('rate_conversation'))

    # Only show feedback if there's a conversation
    # if st.session_state.chat_history:
    # Add download button
    zip_buffer = create_conversation_zip()
    st.sidebar.download_button(
        label=get_translation('download_conversation'),
        data=zip_buffer,
        file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
        mime="application/zip",
        key="download_conversation"
    )

    feedback = st.sidebar.feedback(
        options="stars",
        key="sidebar_rating"
    )

    # Handle feedback submission
    if feedback is not None:
        # Generate a unique message ID for this feedback
        message_id = str(uuid.uuid4())

        # Get detailed feedback if provided
        detailed_feedback = st.sidebar.text_area(
            get_translation('additional_comments'),
            key="sidebar_feedback"
        )

        if st.sidebar.button(get_translation('submit_feedback')):
            store_feedback(
                st.session_state.get("conversation_id", str(uuid.uuid4())),
                message_id,
                feedback,  # feedback will be 1-5 for stars
                detailed_feedback
            )
            st.sidebar.success(get_translation('thank_you_for_feedback'))
            feedback = None
            st.rerun()


def process_question(prompt: str, conn: sqlite3.Connection, schema: str):
    # Generate a unique conversation ID if not exists
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())

    st.session_state.messages = get_context_messages(
        st.session_state.messages, max_messages=st.session_state.max_messages, keep_last_n=st.session_state.keep_last_n
    )

    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    # Process the question
    response, generated_code, result, fig = generate_and_execute(
        prompt, conn, schema)

    # Generate a unique message ID for this response
    message_id = str(uuid.uuid4())

    # Display code if enabled
    if st.session_state.show_generated_code:
        with st.chat_message("assistant"):
            st.write(f"```python\n{generated_code}\n```")

    with st.chat_message("assistant"):
        st.write(response)
        if fig:
            try:
                st.pyplot(fig)
            except Exception:
                pass

        if isinstance(result, pd.DataFrame) and not result.empty:
            st.markdown("**Top Results Preview**")
            st.dataframe(result, height=100)

    # Add response to chat history
    st.session_state.chat_history.append(
        {"role": "assistant", "content": response})

    if fig:
        st.session_state.chat_history.append(
            {"role": "assistant", "content": fig})

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": f"```python\n{generated_code}\n```"
    })
    st.session_state.messages.append(
        {"role": "assistant", "content": f"```python\n{generated_code}\n```\n"+response})


def show_chat_interface_langgraph():
    """
    Show the chat interface using LangGraph
    """
    # Initialize chat interface
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'show_generated_code' not in st.session_state:
        st.session_state.show_generated_code = False

    # Initialize LLMs if they haven't been initialized yet
    if st.session_state.llm_70b is None or st.session_state.llm_8b is None:
        from config import init_llms
        init_llms()

    st.title(get_translation('data_analysis_agent'))

    # Get schema and generate sample questions
    st.session_state.conn, st.session_state.schema = get_sql_schema(
        st.session_state.platform)

    # Show conversation sidebar
    if st.session_state.chat_history:
        show_conversation_sidebar()

    # Initialize or get sample questions from session state
    if 'sample_questions' not in st.session_state or st.session_state.sample_questions is None:
        st.session_state.sample_questions = get_sample_questions(
            st.session_state.platform, st.session_state.language)

    questions = [q.strip()
                 for q in st.session_state.sample_questions.split('\n') if q.strip()]

    with st.expander(get_translation('sample_questions'), expanded=True):
        # Add refresh button in the same row as the expander header
        col1, col2 = st.columns([15, 1])
        with col2:
            if st.button("", icon=":material/refresh:", key="refresh_questions", type="primary"):
                # Generate new questions
                st.session_state.sample_questions = get_sample_questions(
                    st.session_state.platform, st.session_state.language)
                # st.rerun()

        with col1:
            cols = st.columns(5)
            # Take first 5 questions
            for i, question in enumerate(questions[:5]):
                with cols[i]:
                    if st.button(question, key=f"sample_q_{i}"):
                        # Clear chat history before adding new question
                        st.session_state.chat_history = []
                        st.session_state.messages = []
                        # Store the question to be processed after the UI is rendered
                        st.session_state.pending_question = question
                        st.rerun()

    # Display chat history
    for message in st.session_state.chat_history:

        if isinstance(message["content"], str):
            # Only show code snippets if show_generated_code is enabled
            if message["content"].startswith("```python") and not st.session_state.show_generated_code:
                continue
            with st.chat_message(message["role"]):
                st.write(message["content"])
        elif isinstance(message["content"], (pd.DataFrame, pd.Series)):
            with st.chat_message(message["role"]):
                st.dataframe(message["content"], height=100)
        elif isinstance(message["content"], plt.Figure):
            with st.chat_message(message["role"]):
                st.pyplot(message["content"], use_container_width=False)
        else:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # Process any pending question from sample questions
    if hasattr(st.session_state, 'pending_question'):
        with st.spinner(get_translation('processing')):
            process_question(st.session_state.pending_question,
                             st.session_state.conn, st.session_state.schema)
        del st.session_state.pending_question

    # Chat input
    if prompt := st.chat_input("Ask a question about your data"):
        with st.spinner(get_translation('processing')):
            process_question(prompt, st.session_state.conn,
                             st.session_state.schema)
