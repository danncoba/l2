import json
import uuid
from typing import AsyncGenerator, Dict, Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Interrupt
from pydantic import BaseModel

from agents.dto import ChatMessage
from agents.supervisor import (
    get_graph,
    SupervisorState,
    DiscrepancyValues,
    GuidanceValue,
)
from dto.request.testing import TestingRequestBase
from security import admin_required

testing_router = APIRouter(
    prefix="/api/v1/testing", tags=["testing"], dependencies=[Depends(admin_required)]
)


class TestModel(BaseModel):
    name: str
    version: float


@testing_router.post("", response_model=str)
async def test_reasoner(created_dto: TestingRequestBase) -> StreamingResponse:
    first_msg = {
        "message": """
        Expertise Levels in Amazon Web Services
                    Welcome, Oliver! In this discussion, we will explore the various expertise levels available for Amazon Web Services (AWS). Understanding these levels will help you select the appropriate expertise that aligns with your current knowledge and goals.
    
                    Here are the expertise levels you can choose from:
    
                    Not Informed: You have no prior knowledge of AWS.
                    Informed Basics: You have a basic understanding of AWS concepts.
                    Informed in Details: You are knowledgeable about AWS and its services in detail.
                    Practice and Lab Examples: You have hands-on experience with AWS through practical examples and labs.
                    Production Maintenance: You are capable of maintaining AWS services in a production environment.
                    Production from Scratch: You can set up and manage AWS services from the ground up.
                    Educator/Expert: You possess extensive knowledge and can teach others about AWS.
                    Consider your current skills and aspirations as you decide which level best represents your expertise in AWS. Let's dive into the details!
        """,
        "role": "ai",
    }
    state = SupervisorState(
        discrepancy=DiscrepancyValues(
            skill_id=created_dto.discrepancy.skill_id,
            grade_id=created_dto.discrepancy.grade_id,
            user_id=created_dto.discrepancy.user_id,
        ),
        guidance=GuidanceValue(messages=[]),
        next_steps=[],
        messages=[],
        chat_messages=[first_msg] + [m.model_dump() for m in created_dto.messages],
    )
    print(f"SENDING STATE {state}")
    return StreamingResponse(content=run_graph_stream(state), media_type="text/plain")


async def run_graph_stream(state: SupervisorState) -> AsyncGenerator[str, None]:
    async with get_graph() as graph:
        configurable_run = {"configurable": {"thread_id": uuid.uuid4()}}
        state_history = await graph.aget_state(configurable_run)
        print(f"State history {state_history}")
        async for chunk in graph.astream(state, configurable_run):
            print("CHUNK RECEIVED -> ", chunk)
            print(f"CHUNK TYPE {type(chunk)}")
            for key in chunk.keys():
                match key:
                    case "supervisor":
                        yield supervisor_response(chunk[key])
                    case "discrepancy":
                        yield discrepancy_response(chunk[key])
                    case "__interrupt__":
                        yield interrupt_response(chunk[key])


def supervisor_response(supervisor: Dict[str, Any]) -> str:
    print(f"SUPERVISOR -> {supervisor}")
    response = {}
    if "discrepancy" in supervisor:
        if isinstance(supervisor["discrepancy"], DiscrepancyValues):
            response["discrepancy"] = {
                "grade_id": supervisor["discrepancy"].grade_id,
                "skill_id": supervisor["discrepancy"].skill_id,
                "user_id": supervisor["discrepancy"].user_id,
            }
        elif isinstance(supervisor["discrepancy"], dict):
            response["discrepancy"] = supervisor["discrepancy"]
    if "guidance" in supervisor:
        response["guidance"] = []
    if "chat_messages" in supervisor:
        print(f"CHAT MESSAGES {supervisor['chat_messages']}")
        response["messages"] = [
            {"role": msg.role, "message": msg.message.content}
            for msg in supervisor["chat_messages"]
        ]
    full_response = {"supervisor": response}
    return json.dumps(full_response)


def discrepancy_response(discrepancy: Dict[str, Any]) -> str:
    print(f"DISCREPANCY -> {discrepancy}")
    response = {}
    if "discrepancy" in discrepancy:
        if isinstance(discrepancy["discrepancy"], DiscrepancyValues):
            response["discrepancy"] = {
                "grade_id": discrepancy["discrepancy"].grade_id,
                "skill_id": discrepancy["discrepancy"].skill_id,
                "user_id": discrepancy["discrepancy"].user_id,
            }
        elif isinstance(discrepancy["discrepancy"], dict):
            response["discrepancy"] = discrepancy["discrepancy"]
    if "guidance" in discrepancy:
        response["guidance"] = []
    if "chat_messages" in discrepancy:
        response["messages"] = [
            {"role": msg["role"], "message": msg["message"]}
            for msg in discrepancy["chat_messages"]
        ]
    full_response = {"supervisor": response}
    return json.dumps(full_response)


def interrupt_response(interrupt_dict: Dict[str, Any]) -> str:
    print(f"INTERRUPT -> {interrupt_dict}")
    response = {}
    print(f"INTERRUPT DICT TYPE {type(interrupt_dict)}")
    if isinstance(interrupt_dict, tuple):
        print("TUPPPLLEEEEE")
        if isinstance(interrupt_dict[0], Interrupt):
            print("INTERRUPT IS INSTANCE OF INTERRUPT")
            response["messages"] = [interrupt_dict[0].value["answer_to_revisit"]]
    else:
        print("INTERRUPT IS NOT INTERRUPT")
    full_response = {"interrupt": response}
    return json.dumps(full_response)
