import json
import os
import uuid
from typing import List, Any, Literal

import pytest
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from agents.reasoner import reasoner_run
from dto.response.grades import GradeResponseBase
from dto.response.matrix_chats import MessageDict
from utils.common import convert_msg_dict_to_langgraph_format


class TestVals(BaseModel):
    messages: List[dict[Literal["msg_type", "message"], str]]


LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LITE_LLM_URL = os.getenv("OPENAI_BASE_URL")
LITE_MODEL = os.getenv("OPENAI_MODEL")

model = ChatOpenAI(
    model=LITE_MODEL,
    temperature=0,
    api_key=LITE_LLM_API_KEY,
    base_url=LITE_LLM_URL,
    streaming=True,
    verbose=True,
)


grades: List[GradeResponseBase] = [
    GradeResponseBase(id=1, label="Not Informed", value=1),
    GradeResponseBase(id=2, label="Informed Basics", value=2),
    GradeResponseBase(id=3, label="Informed in Details", value=3),
    GradeResponseBase(id=4, label="Practice and Lab Examples", value=4),
    GradeResponseBase(id=5, label="Production Maintenance", value=5),
    GradeResponseBase(id=6, label="Production from Scratch", value=6),
    GradeResponseBase(id=7, label="Educator/Expert", value=7),
]


@pytest.mark.asyncio
async def test_reasoner_run():
    with open("./test_data/full_eval.jsonl", "r") as file:
        for line in file.readlines():
            test_case = TestVals.model_validate_json(line)
            messages = [MessageDict(**m) for m in test_case.messages]
            eval_set = messages[0:-1]
            validation = messages[-1]
            messages_to_send = convert_msg_dict_to_langgraph_format(eval_set)
            async for chunk in reasoner_run(uuid.uuid4(), messages_to_send, grades):
                json_chunk = json.loads(chunk)
                prompt_template = ChatPromptTemplate.from_messages(
                    messages=[
                        SystemMessage(
                            """
                        Do assistant and user message have large similarities between them on the topic and context of the discussion?
                        Respond with exactly "true" (if similar) or exactly "false" (if not similar) only!
                        """
                        ),
                        AIMessage(json_chunk["message"]),
                        HumanMessage(validation.message),
                    ]
                )
                prompt = prompt_template.invoke({})
                response = model.invoke(prompt)
                print(f"Input -> {json_chunk["message"]}")
                print(f"VAL -> {validation.message}")
                print("RESPONSE", response.content)
                assert response.content in ["true", "True"]
