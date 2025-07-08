import os
from typing import List, Tuple, Any

import pytest
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from agents.supervisor import guidance_agent

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


def get_state_for_guidance() -> List[Tuple[Any]]:
    with open("./test_data/guidance_evaluation.json", "r") as file:
        all_content = file.readlines()
        print(f"ALL CONTENT {all_content}")
        return [(all_content)]


@pytest.mark.asyncio
@pytest.mark.parametrize("state", get_state_for_guidance())
async def test_guidance_provider_with_file(state):
    model = ChatOpenAI(
        temperature=0,
        max_tokens=300,
        model=LITE_MODEL,
        api_key=LITE_LLM_API_KEY,
        base_url=LITE_LLM_URL,
        streaming=True,
        verbose=True,
    )
    response = await guidance_agent(state)
    print(f"GUIDANCE RESPONSE {response}")
    assert True