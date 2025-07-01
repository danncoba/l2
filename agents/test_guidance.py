import os
from typing import List

import pytest
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_openai import ChatOpenAI
from mcp.server.fastmcp.prompts.base import UserMessage
from pydantic import BaseModel

from agents.guidance import provide_guidance, GuidanceHelperStdOutput
from dto.response.matrix_chats import MessageDict
from utils.common import convert_msg_dict_to_langgraph_format

load_dotenv()

LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LITE_LLM_URL = os.getenv("OPENAI_BASE_URL")
LITE_MODEL = os.getenv("OPENAI_MODEL")

model = ChatOpenAI(
    temperature=0,
    model=LITE_MODEL,
    api_key=LITE_LLM_API_KEY,
    base_url=LITE_LLM_URL,
    streaming=True,
    verbose=True,
)


class SimilarityResponse(BaseModel):
    are_similar: bool


@pytest.mark.asyncio
async def test_guidance_provider_with_file():
    assert True
