import uuid

from fastapi import APIRouter

from agents.validations_agent import get_graph
from dto.request.matrix_validations import CreateMatrixValidation

matrix_validations_router = APIRouter(
    prefix="/api/v1/matrix-validations", tags=["Matrix Validation"]
)


@matrix_validations_router.post("")
async def validate_matrix(dto: CreateMatrixValidation):
    async with get_graph() as graph:
        configurable_run = {
            "configurable": {"thread_id": uuid.uuid4()},
            "recursion_limit": 10,
        }
        response = await graph.ainvoke(
            {
                "skill_id": 1,
                "difficulty": 4,
                "messages": dto.messages,
                "inner_messages": [],
                "intermediate_steps": [],
            },
            configurable_run,
        )
        return response
