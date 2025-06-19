from typing import List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from routers.dto.response.matrix_chats import MessageDict


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
