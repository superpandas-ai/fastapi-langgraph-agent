import asyncio
from app.core.langgraph.superpandas import SuperpandasAgent
import os
from app.schemas import Message
from app.api.v1.chatbot import chat, ChatRequest, ChatResponse

os.environ["APP_ENV"] = "debug"

# from app.core.langgraph.superpandas.utils import (
#     get_sql_schema,
#     get_sample_questions,
#     get_context_messages,
#     store_feedback,
#     create_conversation_zip
# )

agent = SuperpandasAgent('fic')

query = "How many invoices are in English?"

chat_request = ChatRequest(messages=[Message(role="user", content=query)])


async def main():
    response = await agent.get_response(
        messages=[Message(role="user", content=query)],
        session_id="123",
        user_id="123",
    )

    # response = await chat(chat_request)

    print(response)


if __name__ == "__main__":
    asyncio.run(main())
