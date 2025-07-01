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
    with open("./test_data/guidance_eval.jsonl") as f:
        lines = f.readlines()
        for i in range(0, len(lines), 3):
            ai_line = lines[i]
            human_line = lines[i + 1]
            response = lines[i + 2]
            msg_ai = MessageDict.model_validate_json(ai_line)
            msg_human = MessageDict.model_validate_json(human_line)
            prompt = ChatPromptTemplate.from_messages(messages=[
                SystemMessage(
                    """
                    Do assistant and user message have large similarities between them on the topic and context of the discussion?
                    Respond with json format:
                    are_similar: bool - true (if similar) or false (if not similar) only!
                    """
                ),
                AIMessage(
                    """
                    {ai_msg}
                    """
                ),
                HumanMessage(
                    """
                    {user_msg}
                    """
                )]
            )
            formatted_msgs = convert_msg_dict_to_langgraph_format([msg_ai, msg_human])
            async for chunk in provide_guidance(formatted_msgs):
                print(chunk)
                if chunk.message:
                    msg = prompt.invoke({"ai_msg": response.message, "user_msg": chunk.message})
                    response = model.invoke(msg)
                    parsed_response = SimilarityResponse.model_validate_json(response.content)
                    print("SIMILARITY RESPONSE", parsed_response)
                    assert parsed_response.are_similar


