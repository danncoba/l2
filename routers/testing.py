import json
import uuid
from typing import AsyncGenerator, Dict, Any, Annotated, Optional, List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasicCredentials
from langgraph.types import Interrupt
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agents.supervisor import (
    get_graph,
    SupervisorState,
    DiscrepancyValues,
    GuidanceValue,
)
from agents.welcome import SingleUserSkillData, welcome_agent_batch
from db.db import get_session
from db.models import TestSupervisorMatrix, TestSupervisorWelcome, User
from dto.request.supervisor_matrix import (
    CreateSupervisorMatrixRequest,
    CreateSupervisorWelcomeRequest,
)
from dto.request.testing import TestingRequestBase
from dto.response.matrix_chats import (
    MatrixChatResponseBase,
    MatrixChatResponseSmallBase,
)
from security import admin_required, security, get_current_user
from service.service import BaseService

testing_router = APIRouter(prefix="/api/v1/testing", tags=["testing"])


class TestModel(BaseModel):
    name: str
    version: float


@testing_router.get("/chats", response_model=List[MatrixChatResponseSmallBase])
async def get_testing_chats(
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    current_user: Optional[User] = Depends(get_current_user),
) -> List[MatrixChatResponseBase]:
    service: BaseService[TestSupervisorMatrix, uuid.UUID, Any, Any] = BaseService(
        TestSupervisorMatrix, session
    )
    filters = {
        "user_id": current_user.id,
    }
    all_user_validations = await service.list_all(
        filters=filters, order_by=[TestSupervisorMatrix.created_at.desc()]
    )
    all_matrices: List[MatrixChatResponseSmallBase] = []
    for user_validation in all_user_validations:
        user = await user_validation.awaitable_attrs.user
        skill = await user_validation.awaitable_attrs.skill
        welcome = await user_validation.awaitable_attrs.welcome_msg
        welcome_msg_type = "ai"
        welcome_msg = ""
        if len(welcome) != 0:
            welcome_msg_type = "ai"
            welcome_msg = welcome[0].message

        matrix = MatrixChatResponseSmallBase(
            **user_validation.model_dump(),
            user=user.model_dump(),
            msg_type=welcome_msg_type,
            message=welcome_msg,
            skill=skill.model_dump(),
        )
        all_matrices.append(matrix)
    return all_matrices


@testing_router.get("/chats/{chat_id}", response_model=MatrixChatResponseSmallBase)
async def get_testing_chat(
    chat_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    current_user: Optional[User] = Depends(get_current_user),
) -> MatrixChatResponseBase:
    service: BaseService[TestSupervisorMatrix, uuid.UUID, Any, Any] = BaseService(
        TestSupervisorMatrix, session
    )
    filters = {
        "user_id": current_user.id,
    }
    test_matrice = await service.get(chat_id)
    user = await test_matrice.awaitable_attrs.user
    skill = await test_matrice.awaitable_attrs.skill
    welcome = await test_matrice.awaitable_attrs.welcome_msg
    welcome_msg_type = "ai"
    welcome_msg = ""
    if len(welcome) != 0:
        welcome_msg_type = "ai"
        welcome_msg = welcome[0].message

    matrix = MatrixChatResponseSmallBase(
        **test_matrice.model_dump(),
        user=user.model_dump(),
        msg_type=welcome_msg_type,
        message=welcome_msg,
        skill=skill.model_dump(),
    )

    return matrix


@testing_router.post("/create")
async def create_testing_models():
    async for session in get_session():
        query = text(
            """
            SELECT user_id, skill_id
            FROM users_skills
            EXCEPT
            SELECT user_id, skill_id
            FROM test_supervisor_matrix;
            """
        )

        results = await session.execute(
            query,
        )
        print("TEST VALIDATIONS TOTAL RESULTS ->", results.rowcount)
        all_to_create = []
        ai_batch_data = []
        ai_batch_dict: Dict[int, uuid] = {}
        for result in results:
            chat = CreateSupervisorMatrixRequest(
                id=str(uuid.uuid4()),
                user_id=result[0],
                skill_id=result[1],
            )
            single_user_ai = SingleUserSkillData(
                user_id=result[0],
                skill_id=result[1],
            )
            ai_batch_dict[len(all_to_create)] = chat.id
            all_to_create.append(chat)
            ai_batch_data.append(single_user_ai)
        service: BaseService[
            TestSupervisorMatrix, uuid.UUID, CreateSupervisorMatrixRequest, Any
        ] = BaseService(TestSupervisorMatrix, session)
        welcome_service: BaseService[
            TestSupervisorWelcome, uuid.UUID, CreateSupervisorWelcomeRequest, Any
        ] = BaseService(TestSupervisorWelcome, session)
        print("BEFORE LITELLM BATCH IS INVOLVED")
        welcome_msgs_batch = []
        batch_response = await welcome_agent_batch(ai_batch_data, session)
        for index, msg in enumerate(batch_response):
            create_welcome_msg_req = CreateSupervisorWelcomeRequest(
                id=str(uuid.uuid4()),
                supervisor_matrix_id=ai_batch_dict[index],
                message=msg.choices[0].message["content"],
            )
            welcome_msgs_batch.append(create_welcome_msg_req)
        results = await service.create_many(all_to_create)
        created_welcome_msgs = await welcome_service.create_many(welcome_msgs_batch)

        return batch_response


@testing_router.post("/chats/{chat_id}", response_model=str)
async def reason_through(
    chat_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    created_dto: TestingRequestBase,
    current_user: Optional[User] = Depends(get_current_user),
) -> StreamingResponse:
    service: BaseService[TestSupervisorMatrix, uuid.UUID, Any, Any] = BaseService(
        TestSupervisorMatrix, session
    )
    filters = {
        "user_id": current_user.id,
    }
    test_matrice = await service.get(chat_id)
    user = await test_matrice.awaitable_attrs.user
    skill = await test_matrice.awaitable_attrs.skill
    welcome = await test_matrice.awaitable_attrs.welcome_msg
    welcome_msg_type = "ai"
    welcome_msg = ""
    if len(welcome) != 0:
        welcome_msg_type = "ai"
        welcome_msg = welcome[0].message

    matrix = MatrixChatResponseSmallBase(
        **test_matrice.model_dump(),
        user=user.model_dump(),
        msg_type=welcome_msg_type,
        message=welcome_msg,
        skill=skill.model_dump(),
    )
    state = SupervisorState(
        discrepancy=DiscrepancyValues(
            skill_id=created_dto.discrepancy.skill_id,
            grade_id=created_dto.discrepancy.grade_id,
            user_id=created_dto.discrepancy.user_id,
        ),
        guidance=GuidanceValue(messages=[]),
        next_steps=[],
        messages=[],
        chat_messages=[m.model_dump() for m in created_dto.messages],
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
