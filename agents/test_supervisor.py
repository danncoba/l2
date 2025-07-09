import json
import os
import uuid
from typing import Any, List, Tuple

from dotenv import load_dotenv
import pytest
import pytest_asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from agents.supervisor import supervisor_agent, get_graph

load_dotenv()


LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LITE_LLM_URL = os.getenv("OPENAI_BASE_URL")
LITE_MODEL = os.getenv("OPENAI_MODEL")


def prepare_eval_data() -> List[Tuple[Any]]:
    counter = 0
    with open("./test_data/evaluation.jsonl", "r") as file:
        all_lines = []
        for line in file.readlines():
            all_lines.append((json.loads(line)))
            if counter == 20:
                return all_lines
            counter += 1
        return all_lines


# @pytest.mark.asyncio
# async def test_discrepancy_agent():
#     assert False
#
#
# @pytest.mark.asyncio
# def test_grading_agent():
#     assert False
#
#
# @pytest.mark.asyncio
# def test_guidance_agent():
#     assert False
#
#
# @pytest.mark.asyncio
# def test_feedback_agent():
#     assert False


# @pytest.mark.asyncio
# @pytest.mark.parametrize("state", prepare_eval_data())
# async def test_supervisor_agent(state):
#     model = ChatOpenAI(
#         temperature=0,
#         max_tokens=300,
#         model=LITE_MODEL,
#         api_key=LITE_LLM_API_KEY,
#         base_url=LITE_LLM_URL,
#         streaming=True,
#         verbose=True,
#     )
#     last_message = state["chat_messages"][-1]
#     del state["chat_messages"][-1]
#     print(f"State NOOOOOOOOW {state}")
#     print(f"Last Message NOOOOOOOOW {last_message}")
#     configurable_run = {"configurable": {"thread_id": uuid.uuid4()}}
#     async with get_graph() as graph:
#         response = await graph.ainvoke(state, configurable_run)
#         prompt_template = ChatPromptTemplate.from_template(
#             """
#             Are these messages (First and Second message) similar and do they discuss the same topic?
#             Respond with only true or false!
#             First Message: {first_message}
#             Second Message: {second_message}:
#             """
#         )
#         print(f"Response NOOOOOOOOW {response}")
#         print(
#             f"Messages comparison:\n{last_message['message']}\n{response['chat_messages'][-1]['message']}"
#         )
#         prompt = await prompt_template.ainvoke(
#             {
#                 "first_message": last_message["message"],
#                 "second_message": response["chat_messages"][-1]["message"],
#             }
#         )
#
#         are_similar = await model.ainvoke(prompt)
#         assert are_similar.content in ["true", "True"]
