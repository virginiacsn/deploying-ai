from assignment_chat.main import get_graph
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages.utils import filter_messages

import warnings
warnings.filterwarnings("ignore", message=".*HTTP_422_UNPROCESSABLE_ENTITY.*")
import gradio as gr

from assignment_chat.prompts import SYSTEM_PROMPT_REPLY
from assignment_chat.embedding import SRC_DIR

from dotenv import load_dotenv
from utils.logger import get_logger

_logs = get_logger(__name__)

load_dotenv(SRC_DIR / ".secrets")

graph = get_graph()

def clinical_chat(message: str, history: list[dict]) -> str:
    langchain_messages = []
    for msg in history:
        if msg['role'] == 'user':
            langchain_messages.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            if SYSTEM_PROMPT_REPLY in str(msg['content']):
                langchain_messages[-1].name = "off_topic"
                langchain_messages.append(AIMessage(content=msg['content'], name="off_topic"))
            else:
                langchain_messages.append(AIMessage(content=msg['content']))
    langchain_messages.append(HumanMessage(content=message))

    filtered = filter_messages(
        langchain_messages,
        exclude_names=["off_topic"]
    )

    state = {"messages": filtered}
    response = graph.invoke(state)
    llm_message = response['messages'][len(response['messages']) - 1].content

    _logs.debug(f"HumanMessage: {message}")
    new_messages = response['messages'][len(filtered):]
    for msg in new_messages:
        for tool_call in getattr(msg, "tool_calls", None) or []:
            _logs.debug(f"ToolCall: {tool_call['name']} args={tool_call['args']}")
    _logs.debug(f"AIMessage: {llm_message}")

    return llm_message

chat = gr.ChatInterface(
    fn=clinical_chat
)

if __name__ == "__main__":
    _logs.info('Launching clinical app...')
    try:
        chat.launch()
    except KeyboardInterrupt:
        _logs.info("Shutting down...")
    except Exception as e:
        _logs.error(f"Error: {e}")
    finally:
        chat.close()
