from dotenv import load_dotenv
from inspect_ai import Task, task
from inspect_ai.dataset import csv_dataset
from inspect_ai.scorer import model_graded_fact
from inspect_ai.solver import self_critique, generate

DATASET_ID="cmdeekh9m00auyrs5etr9ccyf"


load_dotenv()


@task
def example_eval():
    return Task(
        dataset=csv_dataset(f"langtracefs://{DATASET_ID}"),
        plan=[
            generate(),
            self_critique(model="openai/l2-gpt-4o")
        ],
        scorer=model_graded_fact()
    )
