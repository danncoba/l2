import os
from typing import List

import pytest
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from agents.guidance import provide_guidance, GuidanceHelperStdOutput
from dto.response.matrix_chats import MessageDict
from utils.common import convert_msg_dict_to_langgraph_format

load_dotenv()

LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LITE_LLM_URL = os.getenv("OPENAI_BASE_URL")
LITE_MODEL = os.getenv("OPENAI_MODEL")

model = ChatOpenAI(
    model=LITE_MODEL,
    api_key=LITE_LLM_API_KEY,
    base_url=LITE_LLM_URL,
    streaming=True,
    verbose=True,
)

@pytest.mark.asyncio
async def test_guidance_provider_with_file():
    with open("../test_data/guidance_eval.jsonl") as f:
        lines = f.readlines()
        for i in range(0, len(lines), 2):
            ai_line = lines[i]
            human_line = lines[i + 1]
            msg_ai = MessageDict.model_validate_json(ai_line)
            msg_human = MessageDict.model_validate_json(human_line)
            formatted_msgs = convert_msg_dict_to_langgraph_format([msg_ai, msg_human])
            async for chunk in provide_guidance(formatted_msgs):
                print(chunk)
                assert chunk.has_user_answered

