from langgraph.graph import StateGraph, MessagesState, START
from langchain.chat_models import init_chat_model
from langgraph.prebuilt.tool_node import ToolNode, tools_condition
from langchain_core.messages import SystemMessage
from langchain_core.messages.utils import trim_messages, count_tokens_approximately

from assignment_chat.prompts import get_system_prompt
from assignment_chat.tools import get_matching_trials, get_clinical_trial, get_pubmed_articles
from assignment_chat.embedding import SRC_DIR

import os
from dotenv import load_dotenv
from utils.logger import get_logger


_logs = get_logger(__name__)
load_dotenv(SRC_DIR / ".env")
load_dotenv(SRC_DIR / ".secrets")


llm = init_chat_model(
    "openai:gpt-4o-mini",
    base_url='https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1', 
    api_key='any value',
    default_headers={"x-api-key": os.getenv('API_GATEWAY_KEY')}
)

tools = [get_matching_trials, get_clinical_trial, get_pubmed_articles]

system_prompt = get_system_prompt()
_logs.debug(f"Prompt: {system_prompt}")


def call_assistant(state: MessagesState):
    """LLM decides whether to call a tool or not"""

    trimmed = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=60000,
        start_on="human",
    )

    response = llm.bind_tools(tools).invoke([SystemMessage(content=system_prompt)] + trimmed)
    return {
        "messages": [response]
    }

def get_graph():
    builder = StateGraph(MessagesState)
    builder.add_node(call_assistant)
    builder.add_node(ToolNode(tools))
    builder.add_edge(START, "call_assistant")
    builder.add_conditional_edges(
        "call_assistant",
        tools_condition,
    )
    builder.add_edge("tools", "call_assistant")
    graph = builder.compile()
    return graph
