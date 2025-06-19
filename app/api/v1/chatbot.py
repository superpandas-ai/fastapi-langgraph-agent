"""Chatbot API endpoints for handling chat interactions.

This module provides endpoints for chat interactions, including regular chat,
streaming chat, message history management, and chat history clearing.
"""

import json
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from fastapi.responses import StreamingResponse
from app.core.metrics import llm_stream_duration_seconds
from app.api.v1.auth import get_current_session
from app.core.config import settings
# from app.core.langgraph.graph import LangGraphAgent
from app.core.langgraph.superpandas import SuperpandasAgent
from app.core.limiter import limiter
from app.core.logging import logger
from app.models.session import Session
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    StreamResponse,
    AgentSelection,
)

router = APIRouter()
fic_agent = SuperpandasAgent('fic')
sevdesk_agent = SuperpandasAgent('sevdesk')
hr_agent = SuperpandasAgent('hr')

agents = {
    "fic": fic_agent,
    "sevdesk": sevdesk_agent,
    "hr": hr_agent,
}


def get_agent(session: Session, platform: Optional[str] = None) -> SuperpandasAgent:
    """Get the appropriate agent based on session or platform.

    Args:
        session: The current session
        platform: Optional platform override

    Returns:
        SuperpandasAgent: The selected agent

    Raises:
        HTTPException: If no agent is selected or invalid platform
    """
    if platform:
        if platform not in agents:
            raise HTTPException(
                status_code=400, detail=f"Invalid platform: {platform}")
        return agents[platform]

    if not session.selected_agent:
        raise HTTPException(
            status_code=400, detail="No agent selected. Please select an agent first.")

    if session.selected_agent not in agents:
        raise HTTPException(
            status_code=400, detail=f"Invalid selected agent: {session.selected_agent}")

    return agents[session.selected_agent]


@router.post("/select-agent")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["chat"][0])
async def select_agent(
    request: Request,
    agent_selection: AgentSelection,
    session: Session = Depends(get_current_session),
):
    """Select an agent for the current session.

    Args:
        request: The FastAPI request object for rate limiting.
        agent_selection: The agent selection request.
        session: The current session from the auth token.

    Returns:
        dict: A message indicating the agent was selected.

    Raises:
        HTTPException: If the agent selection is invalid.
    """
    if agent_selection.platform not in agents:
        raise HTTPException(
            status_code=400, detail=f"Invalid platform: {agent_selection.platform}")

    session.selected_agent = agent_selection.platform
    await session.save()

    return {"message": f"Agent {agent_selection.platform} selected successfully"}


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["chat"][0])
async def chat(
    request: Request,
    chat_request: ChatRequest,
    session: Session = Depends(get_current_session),
):
    """Process a chat request using LangGraph.

    Args:
        request: The FastAPI request object for rate limiting.
        chat_request: The chat request containing messages.
        session: The current session from the auth token.

    Returns:
        ChatResponse: The processed chat response.

    Raises:
        HTTPException: If there's an error processing the request.
    """
    agent = get_agent(session, chat_request.platform)

    try:
        logger.info(
            "chat_request_received",
            session_id=session.id,
            message_count=len(chat_request.messages),
        )

        chat_response = await agent.get_response(
            chat_request.messages, session.id, user_id=session.user_id
        )

        logger.info("chat_request_processed", session_id=session.id)

        return chat_response
    except Exception as e:
        logger.error("chat_request_failed", session_id=session.id,
                     error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["chat_stream"][0])
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    session: Session = Depends(get_current_session),
):
    """Process a chat request using LangGraph with streaming response.

    Args:
        request: The FastAPI request object for rate limiting.
        chat_request: The chat request containing messages.
        session: The current session from the auth token.

    Returns:
        StreamingResponse: A streaming response of the chat completion.

    Raises:
        HTTPException: If there's an error processing the request.
    """
    agent = get_agent(session, chat_request.platform)

    try:
        logger.info(
            "stream_chat_request_received",
            session_id=session.id,
            message_count=len(chat_request.messages),
        )

        async def event_generator():
            """Generate streaming events.

            Yields:
                str: Server-sent events in JSON format.

            Raises:
                Exception: If there's an error during streaming.
            """
            try:
                full_response = ""
                with llm_stream_duration_seconds.labels(model=agent.llm.model_name).time():
                    async for chunk in agent.get_stream_response(
                        chat_request.messages, session.id, user_id=session.user_id
                    ):
                        full_response += chunk
                        response = StreamResponse(content=chunk, done=False)
                        yield f"data: {json.dumps(response.model_dump())}\n\n"

                # Send final message indicating completion
                final_response = StreamResponse(content="", done=True)
                yield f"data: {json.dumps(final_response.model_dump())}\n\n"

            except Exception as e:
                logger.error(
                    "stream_chat_request_failed",
                    session_id=session.id,
                    error=str(e),
                    exc_info=True,
                )
                error_response = StreamResponse(content=str(e), done=True)
                yield f"data: {json.dumps(error_response.model_dump())}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        logger.error(
            "stream_chat_request_failed",
            session_id=session.id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def get_session_messages(
    request: Request,
    session: Session = Depends(get_current_session),
):
    """Get all messages for a session.

    Args:
        request: The FastAPI request object for rate limiting.
        session: The current session from the auth token.

    Returns:
        ChatResponse: All messages in the session.

    Raises:
        HTTPException: If there's an error retrieving the messages.
    """
    agent = get_agent(session)

    try:
        messages = await agent.get_chat_history(session.id)
        return ChatResponse(messages=messages)
    except Exception as e:
        logger.error("get_messages_failed", session_id=session.id,
                     error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/messages")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def clear_chat_history(
    request: Request,
    session: Session = Depends(get_current_session),
):
    """Clear all messages for a session.

    Args:
        request: The FastAPI request object for rate limiting.
        session: The current session from the auth token.

    Returns:
        dict: A message indicating the chat history was cleared.
    """
    agent = get_agent(session)

    try:
        await agent.clear_chat_history(session.id)
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        logger.error("clear_chat_history_failed",
                     session_id=session.id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
