from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from pydantic import BaseModel


class MatrixValidationsResponse(BaseModel):
    messages: list[HumanMessage | AIMessage | SystemMessage | ToolMessage]
