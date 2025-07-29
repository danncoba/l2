from dotenv import load_dotenv
from inspect_ai import Task, task
from inspect_ai.dataset import csv_dataset
from inspect_ai.scorer import model_graded_fact, includes, scorer, Scorer
from inspect_ai.solver import self_critique, generate, chain_of_thought

from agents.validations_agent import get_graph

DATASET_ID = "cmdeekh9m00auyrs5etr9ccyf"
FULL_EVAL_DATASET_ID = "cmdoedhqj00l1yrs5ix70ddfn"


load_dotenv()

from inspect_ai.solver import Solver, solver


@solver
def langgraph_solver():
    async def solve(state, generate):
        async with get_graph() as graph:
            result = await graph.ainvoke(state)
            return result

    return solve


@scorer
def langgraph_scorer() -> Scorer:
    pass


# @task
# def full_flow_evaluation():
#     return Task(
#         dataset=csv_dataset(f"langtracefs://{DATASET_ID}"),
#         plan=[
#             chain_of_thought(),
#             generate(),
#             self_critique(model="openai/l2-gpt-4o")
#         ],
#         scorer=model_graded_fact()
#     )


@task
def full_eval():
    return Task(
        dataset=csv_dataset(f"langtracefs://{FULL_EVAL_DATASET_ID}"),
        plan=[langgraph_solver()],
        scorer=includes(
            "user_answered",
        ),
    )
