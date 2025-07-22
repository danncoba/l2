from typing import List

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    BaseMessage,
    ToolMessage,
)

from agents.dto import AgentMessage, ChatMessage
from dto.request.testing import MessagesRequestBase
from dto.response.matrix_chats import MessageDict


async def common_parameters(offset: int = 0, limit: int = 20, order_by: List[str] = []):
    return {"offset": offset, "limit": limit, "order_by": order_by}


def convert_msg_dict_to_langgraph_format(
    msgs: List[MessageDict],
) -> List[AIMessage | HumanMessage | SystemMessage]:
    langchain_msgs: List[AIMessage | HumanMessage | SystemMessage] = []
    for msg in msgs:
        if msg.msg_type == "ai":
            langchain_msgs.append(AIMessage(msg.message))
        elif msg.msg_type == "human":
            langchain_msgs.append(HumanMessage(msg.message))
        elif msg.msg_type == "system":
            langchain_msgs.append(SystemMessage(msg.message))

    return langchain_msgs


def convert_agent_msg_to_llm_message(
    agent_msgs: List[AgentMessage],
) -> List[AIMessage | HumanMessage | SystemMessage]:
    langchain_msgs: List[AgentMessage | HumanMessage | SystemMessage] = []
    counter = 0
    for agent_msg in agent_msgs:
        if counter == 0 or counter % 2 == 0:
            langchain_msgs.append(AIMessage(agent_msg.message.content))
        else:
            langchain_msgs.append(HumanMessage(agent_msg.message.content))
        counter += 1
    return langchain_msgs


def convert_chat_messages_to_llm_message(
    chat_msgs: List[ChatMessage],
) -> List[BaseMessage]:
    langchain_msgs: List[BaseMessage] = []
    for chat_msg in chat_msgs:
        if chat_msg.role == "user":
            langchain_msgs.append(HumanMessage(chat_msg.content))
        elif chat_msg.role == "assistant":
            langchain_msgs.append(AIMessage(chat_msg.content))
        elif chat_msg.role == "system":
            langchain_msgs.append(SystemMessage(chat_msg.content))
    return langchain_msgs


def convert_msg_request_to_llm_messages(
    messages: List[MessagesRequestBase],
) -> List[AIMessage | HumanMessage | ToolMessage | SystemMessage]:
    msgs = [
        AIMessage(msg.message) if msg.role == "ai" else HumanMessage(msg.message)
        for msg in messages
    ]
    return msgs
