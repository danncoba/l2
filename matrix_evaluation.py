import os
import uuid
import json

from dotenv import load_dotenv
from inspect_ai import Task, task, Epochs
from inspect_ai.dataset import csv_dataset
from inspect_ai.scorer import (
    scorer,
    Score,
    CORRECT,
    INCORRECT,
    Target,
    accuracy,
    stderr,
    mean,
)
from inspect_ai.solver import solver, TaskState
from typing import TypedDict, Optional, Annotated
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from langtrace_python_sdk import langtrace

from dto.request.testing import MessagesRequestBase


class MatrixValidationState(TypedDict):
    model: str
    question_id: int
    question: str
    answer: str
    rules: Optional[str]
    inner_messages: Annotated[list, add_messages]
    guidance_questions: Annotated[list, add_messages]
    messages: Annotated[list, add_messages]
    guidance_amount: int
    next: Annotated[list, add_messages]


load_dotenv()

LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LITE_LLM_URL = os.getenv("OPENAI_BASE_URL")
LITE_MODEL = os.getenv("OPENAI_MODEL")
LITE_OPENAI_O3_MODEL = os.getenv("LITE_OPENAI_O3_MODEL")

LANGTRACE_API_KEY = os.getenv("LANGTRACE_API_KEY")
LANGTRACE_HOST = os.getenv("LANGTRACE_HOST")

from agents.validations_agent import get_graph, LLMFormatError

langtrace.init(api_key=LANGTRACE_API_KEY, api_host=LANGTRACE_HOST)


@solver
def matrix_validation_solver():
    async def solve(state: TaskState, generate):
        try:
            input_data: MatrixValidationState = json.loads(state.input_text)
            msgs_typed = []
            for msg in input_data["messages"]:
                typed_msg = MessagesRequestBase(
                    role=msg["role"], message=msg["content"]
                )
                msgs_typed.append(typed_msg)
            input_data["messages"] = msgs_typed
            input_data["safety_response"] = None
            print(input_data)
        except json.JSONDecodeError as e:
            print(f"JSON Error: {e}")
            print(f"Input text: {state.input_text}")
            state.output.completion = "JSON parsing error"
            return state

        async with get_graph() as graph:
            configurable = {
                "configurable": {"thread_id": uuid.uuid4()},
            }
            try:
                result = await graph.ainvoke(input_data, configurable)
            except LLMFormatError as e:
                result = await graph.ainvoke(input_data, configurable)

        # Extract final response
        if result.get("messages"):
            final_message = result["messages"][-1]
            response = final_message.message
        else:
            response = str(result)

        state.output.completion = response
        return state

    return solve


@scorer(metrics=[accuracy(), mean(), stderr()])
def matrix_validation_scorer():
    async def score(state: TaskState, target: Target):
        response = state.output.completion.lower()
        expected = target.text.lower()
        template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
            You are matching do the user message and ai message are similar in meaning!
            Content itself does not need to match, the meaning has to be similar or same for them to be declared
            as similar!
            Most important part is completeness percentage or grade. 
            Biggest allowed difference between assistant and users completeness score or grade can be 15% to think of them as similar!
            If assistant completeness score is less than users, then the allowed difference is 30% at most!
            
            Respond in json format without additional explanations:
            is_similar: boolean, whether they are similar or not
            """,
                ),
                (
                    "human",
                    """
             {expected}
             """,
                ),
                (
                    "ai",
                    """
             {actual}
             """,
                ),
            ]
        )
        prompt = await template.ainvoke({"expected": expected, "actual": response})
        model = ChatOpenAI(
            model=LITE_MODEL,
            base_url=LITE_LLM_URL,
            api_key=LITE_LLM_API_KEY,
            temperature=0,
            top_p=1,
            max_tokens=50,
            stop_sequences=["\nObservation: "],
        )
        result = await model.ainvoke(prompt)
        content = result.content
        if content.startswith("```json"):
            content = content.strip("```json").strip("```")
        result_in_json = json.loads(content)
        if result_in_json["is_similar"]:
            return Score(value=CORRECT, answer=response)

        return Score(value=INCORRECT, answer=response)

    return score


@task
def matrix_validation_eval():
    return Task(
        dataset=csv_dataset("evaluation_dataset_misbehaving.csv"),
        plan=[matrix_validation_solver()],
        scorer=matrix_validation_scorer(),
        fail_on_error=False,
        epochs=Epochs(1, ["mean"]),
    )
