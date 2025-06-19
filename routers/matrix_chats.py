import uuid
from typing import Annotated, Any, AsyncGenerator, Coroutine, List

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasicCredentials
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import StateSnapshot
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import StreamingResponse

from agents.reasoner import reasoner_run, get_graph, run_interrupted
from agents.welcome import welcome_agent
from routers.db.db import get_session
from routers.db.models import Grade, MatrixChat, Notification, UserSkills
from routers.dto.inner.matrix_chat import UpdateMatrixChatStatusBase
from routers.dto.inner.notifications import CreateNotificationRequestBase
from routers.dto.inner.user_skills import UpdateUserSkillsRequest
from routers.dto.request.matrix_chat import (
    MatrixChatRequestBase,
    MatrixChatInterruptRequestBase,
)
from routers.dto.response.common import ActionSuccessResponse
from routers.dto.response.grades import GradeResponseBase
from routers.dto.response.matrix_chats import (
    MatrixChatResponseBase,
    MatrixMessageChatResponse,
    MessageDict,
)
from routers.service.service import BaseService
from routers.utils.common import convert_msg_dict_to_langgraph_format
from security import security

matrix_chats_router = APIRouter(
    prefix="/api/v1/matrix-chats", tags=["Matrix Validations Chat"]
)


async def send_msg_by_msg(msgs: List[MessageDict]):
    for msg in msgs:
        yield msg.model_dump_json()


@matrix_chats_router.get("/{chat_id}/info", response_model=None)
async def get_matrix_chat_info(
    chat_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> MatrixChatResponseBase:
    service: BaseService[MatrixChat, uuid.UUID, Any, Any] = BaseService(
        MatrixChat, session
    )
    chat = await service.get(chat_id)
    user = await chat.awaitable_attrs.user
    skill = await chat.awaitable_attrs.skill
    return MatrixChatResponseBase(
        **chat.model_dump(), user=user.model_dump(), skill=skill.model_dump()
    )


@matrix_chats_router.get("/{chat_id}", response_model=None)
async def get_matrix_chat(
    chat_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> None | StreamingResponse:
    service: BaseService[MatrixChat, uuid.UUID, Any, Any] = BaseService(
        MatrixChat, session
    )
    async for graph in get_graph():
        config = {"configurable": {"thread_id": chat_id}}
        messages = []
        chat = await service.get(chat_id)
        user = await chat.awaitable_attrs.user
        skill = await chat.awaitable_attrs.skill
        state = await graph.aget_state(config)
        print(f"STATE {state}")
        if len(state.values) > 0:
            for msg in state.values["messages"]:
                print("MSG -> ", msg)
                if isinstance(msg, AIMessage):
                    messages.append(
                        MessageDict(
                            msg_type="ai",
                            message=msg.content,
                            are_separate_messages=True,
                        )
                    )
                elif isinstance(msg, HumanMessage):
                    messages.append(
                        MessageDict(
                            msg_type="human",
                            message=msg.content,
                            are_separate_messages=True,
                        )
                    )
                elif isinstance(msg, SystemMessage):
                    messages.append(
                        MessageDict(
                            msg_type="system",
                            message=msg.content,
                            are_separate_messages=True,
                        )
                    )
        else:
            return StreamingResponse(
                welcome_agent(user.id, skill.id, session), media_type="application/json"
            )

        return StreamingResponse(
            send_msg_by_msg(messages), media_type="application/json"
        )


@matrix_chats_router.post("/{chat_id}", response_model=MessageDict)
async def post_matrix_message(
    chat_id: uuid.UUID,
    create_dto: MatrixChatRequestBase,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> MessageDict:
    chat_service: BaseService[
        MatrixChat, uuid.UUID, Any, UpdateMatrixChatStatusBase
    ] = BaseService(MatrixChat, session)
    service: BaseService[Grade, int, Any, Any] = BaseService(Grade, session)
    notification_service: BaseService[
        Notification, int, CreateNotificationRequestBase, Any
    ] = BaseService(Notification, session)
    user_skill_service: BaseService[UserSkills, int, Any, UpdateUserSkillsRequest] = (
        BaseService(UserSkills, session)
    )
    current_chat = await chat_service.get(chat_id)
    if current_chat.status == "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden to modify completed discussion",
        )
    grades = await service.list_all()
    all_grades = []
    for grade in grades:
        all_grades.append(GradeResponseBase(**grade.model_dump()))
    state = await get_current_state(chat_id)
    messages_to_send = []
    grades_to_send = []
    print(f"STATE VALUES {state.values}")
    if "messages" in state.values and "grades" in state.values:
        messages_to_send = state.values["messages"] + [
            HumanMessage(create_dto.messages[-1].message)
        ]
        grades_to_send = state.values["grades"]
    else:
        messages_to_send = convert_msg_dict_to_langgraph_format(create_dto.messages)
        grades_to_send = all_grades
    response = await reasoner_run(chat_id, messages_to_send, grades_to_send)
    print("RESPONSE REASONER -> ", response)
    if response["interrupt_happened"]:
        print("INTERRUPT HAPPENED RESPONSE {response}")
        notification_request = CreateNotificationRequestBase(
            notification_type="INTERRUPT",
            user_id=None,
            status="UNREAD",
            chat_uuid=chat_id,
            message=response["message"],
            user_group="ADMIN",
        )
        await notification_service.create(notification_request)
        return MessageDict(
            msg_type="ai",
            message=response["message"],
            is_execution_blocked=True,
            is_ambiguous=True,
        )
    else:
        await chat_service.update(
            chat_id, UpdateMatrixChatStatusBase(status="COMPLETED")
        )
        filters = {
            "user_id": current_chat.user_id,
            "skill_id": current_chat.skill_id,
        }
        user_skill = await user_skill_service.list_all(
            filters=filters, limit=1, offset=0
        )
        if len(user_skill) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User Skill not found",
            )
        await user_skill_service.update(
            user_skill[0].id,
            UpdateUserSkillsRequest(grade_id=response["final_result"].final_class_id),
        )

    return MessageDict(
        msg_type="ai",
        message=response["message"],
    )


@matrix_chats_router.post("/{chat_id}/interrupt", response_model=MessageDict)
async def post_interrupt_resolution(
    chat_id: uuid.UUID,
    create_dto: MatrixChatInterruptRequestBase,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> MessageDict:
    service: BaseService[Grade, int, Any, Any] = BaseService(Grade, session)
    notification_service: BaseService[
        Notification, int, CreateNotificationRequestBase, Any
    ] = BaseService(Notification, session)
    await run_interrupted(chat_id, create_dto.grade)
    return MessageDict(
        msg_type="admin_user",
        message="Successfully resolved the unknown answer",
        is_execution_blocked=False,
        are_separate_messages=True,
    )


async def get_current_state(thread_id: uuid.UUID) -> StateSnapshot | None:
    async for graph in get_graph():
        config = {"configurable": {"thread_id": thread_id}}
        current_state = await graph.aget_state(config)
        return current_state
