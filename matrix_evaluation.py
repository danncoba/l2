import pprint
import sys
import os
import uuid
import json

from langtrace_python_sdk import langtrace

from dto.request.testing import MessagesRequestBase

sys.path.insert(0, '/Users/danijeldjuric/Desktop/Projects/Solutions/l2work')

from dotenv import load_dotenv
from inspect_ai import Task, task
from inspect_ai.dataset import csv_dataset
from inspect_ai.scorer import scorer, Score, CORRECT, INCORRECT, Target, accuracy
from inspect_ai.solver import solver, TaskState
from typing import TypedDict, Optional, Annotated
from langgraph.graph.message import add_messages

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
                    role=msg["role"],
                    message=msg["content"]
                )
                msgs_typed.append(typed_msg)
            input_data["messages"] = msgs_typed
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

@scorer(metrics=[accuracy()])
def matrix_validation_scorer():
    async def score(state: TaskState, target: Target):
        print(f"SCORE STATE {state}")
        response = state.output.completion.lower()
        expected = target.text.lower()
        
        # Simple keyword matching for evaluation categories
        evaluation_keywords = {
            "correct": ["correct", "accurate", "comprehensive", "good understanding"],
            "partial": ["partial", "incomplete", "missing", "basic understanding"],
            "incorrect": ["incorrect", "wrong", "misunderstood", "confused"]
        }
        
        # Check if response aligns with expected evaluation
        for category, keywords in evaluation_keywords.items():
            if category in expected:
                if any(keyword in response for keyword in keywords):
                    return Score(value=CORRECT, answer=response)
        
        return Score(value=INCORRECT, answer=response)
    
    return score

@task
def matrix_validation_eval():
    return Task(
        dataset=csv_dataset("evaluation_dataset.csv"),
        plan=[matrix_validation_solver()],
        scorer=matrix_validation_scorer(),
        fail_on_error=False
    )