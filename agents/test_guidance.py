import csv
import json
import pytest
import os
from typing import List, Tuple, Any

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from agents.supervisor import guidance_agent

load_dotenv()

LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LITE_LLM_URL = os.getenv("OPENAI_BASE_URL")
LITE_MODEL = os.getenv("OPENAI_MODEL")


class JsonResponse(BaseModel):
    is_response_correct: bool
    response_reason: str


class SimilarityResponse(BaseModel):
    are_similar: bool


def get_state_for_guidance() -> List[Tuple[Any]]:
    with open("./test_data/guidance_evaluation.jsonl", "r") as file:
        params = []
        all_content = file.readlines()
        for line in all_content:
            params.append((json.loads(line)))
        return params


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
    all_messages = [
        (
            HumanMessage(msg["message"])
            if msg["role"] == "human"
            else AIMessage(msg["message"])
        )
        for msg in response["chat_messages"]
    ]
    guidance_msg = [
        msg.message if msg.role == "guidance" else None for msg in response["messages"]
    ]
    prompt_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                """
            Does the last message respond correctly to the user?
            Respond exactly with the following json schema:
            is_response_correct: boolean // whether the response is responding correctly to the user
            response_reason: str // the reasoning why it's correct or not correct
            """
            ),
            *all_messages,
            *guidance_msg,
        ]
    )
    print(f"ALLL MESSAGES {all_messages}")
    print(f"PROMPT TEMPLATE {prompt_template}")
    prompt = await prompt_template.ainvoke({})

    are_similar = await model.ainvoke(prompt)

    print(f"GUIDANCE TEST RESPONSE {response}")
    json_response = JsonResponse.model_validate_json(are_similar.content)
    print(f"JSON RESPONSE {json_response}")
    with open("output.csv", "a", newline="") as file:
        writer = csv.writer(file)
        msgs_content = "\n\n--->\n".join([msg.content for msg in all_messages])
        msgs_guidance = "\n\n--->\n".join([msg.content for msg in guidance_msg])
        data = [[msgs_content, msgs_guidance, are_similar.model_dump_json()]]
        writer.writerows(data)
    assert json_response.is_response_correct
