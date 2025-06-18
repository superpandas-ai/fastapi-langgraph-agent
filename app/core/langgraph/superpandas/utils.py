
from pathlib import Path
import sqlite3
import streamlit as st
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

base_path = Path("app/core/langgraph/superpandas/")


def get_sql_schema(platform: str) -> tuple[sqlite3.Connection, str]:
    db_path = Path(base_path, 'databases', platform+'.db')
    sql_path = Path(base_path, 'databases', platform+'.sql')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    with open(sql_path, 'r') as f:
        sql_schema = f.read()
        sql_schema = ''.join(sql_schema)
    return conn, sql_schema


def summarize_history(messages, keep_last_n=6):
    if len(messages) <= keep_last_n:
        return messages
    summary_prompt = PromptTemplate.from_template(
        "Summarize the following conversation history for future reference:\n{history}"
    )
    history_text = "\n".join([msg["content"]
                             for msg in messages[:-keep_last_n]])
    summary_chain = summary_prompt | st.session_state.llm_70b | StrOutputParser()
    summary = summary_chain.invoke({"history": history_text})

    last_system_message = messages[0] if messages[0]["role"] == "system" else ""
    summarized_messages = [
        {
            "role": "system",
            "content": f"{last_system_message['content']}\n\nHere is a summary of previous conversation: {summary}",
        }
    ] + messages[-keep_last_n:]

    print(f"DEBUG - Summarized messages: {summarized_messages}")
    return summarized_messages


def get_context_messages(messages, max_messages=12, keep_last_n=6):
    if len(messages) > max_messages:
        assert keep_last_n <= max_messages, "keep_last_n must be less than or equal to max_messages"
        return summarize_history(messages, keep_last_n=keep_last_n)
    return messages
