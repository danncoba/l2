from typing import Union, Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    message: Union[str, AIMessage, HumanMessage, SystemMessage]
    role: str = Field(description="Role of the agent")


class ChatMessage(BaseModel):
    message: Union[str, AIMessage, HumanMessage, SystemMessage]
    role: Literal["human", "ai", "admin"] = Field(description="Type of messages")
