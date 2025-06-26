import json
import uuid
from typing import Annotated, Any, List, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasicCredentials
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import StateSnapshot
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from agents.reasoner import (
    reasoner_run,
    get_graph,
    run_interrupted,
    FinalClassificationStdOutput,
)
from agents.welcome import welcome_agent
from db.db import get_session
from db.models import Grade, MatrixChat, Notification, UserSkills
from dto.inner.matrix_chat import UpdateMatrixChatStatusBase
from dto.inner.notifications import CreateNotificationRequestBase
from dto.inner.user_skills import UpdateUserSkillsRequest
from dto.request.matrix_chat import (
    MatrixChatRequestBase,
    MatrixChatInterruptRequestBase,
)
from dto.response.grades import GradeResponseBase
from dto.response.matrix_chats import (
    MatrixChatResponseBase,
    MessageDict,
)
from security import security
from service.service import BaseService
from utils.common import convert_msg_dict_to_langgraph_format

matrix_chats_router = APIRouter(
    prefix="/api/v1/matrix-chats", tags=["Matrix Validations Chat"]
)


async def send_msg_by_msg(msgs: List[MessageDict]):
    for msg in msgs:
        yield msg.model_dump_json()


@matrix_chats_router.get(
    "/users/{user_id}", response_model=List[MatrixChatResponseBase]
)
async def get_matrix_users_chats(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> List[MatrixChatResponseBase]:
    service: BaseService[MatrixChat, uuid.UUID, Any, Any] = BaseService(
        MatrixChat, session
    )
    filters = {
        "user_id": user_id,
    }
    all_user_validations = await service.list_all(
        filters=filters, order_by=[MatrixChat.created_at.desc()]
    )
    all_matrices: List[MatrixChatResponseBase] = []
    for user_validation in all_user_validations:
        user = await user_validation.awaitable_attrs.user
        skill = await user_validation.awaitable_attrs.skill
        matrix = MatrixChatResponseBase(
            **user_validation.model_dump(),
            user=user.model_dump(),
            skill=skill.model_dump(),
        )
        all_matrices.append(matrix)
    return all_matrices


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
    async with get_graph() as graph:
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


@matrix_chats_router.post("/{chat_id}", response_model=None)
async def post_matrix_message(
    chat_id: uuid.UUID,
    create_dto: MatrixChatRequestBase,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> StreamingResponse:
    chat_service: BaseService[
        MatrixChat, uuid.UUID, Any, UpdateMatrixChatStatusBase
    ] = BaseService(MatrixChat, session)
    service: BaseService[Grade, int, Any, Any] = BaseService(Grade, session)
    current_chat = await chat_service.get(chat_id)
    if current_chat.status == "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden to modify completed discussion",
        )
    grades = await service.list_all()
    all_grades = []
    for grade in grades:
        all_grades.append(grade.model_dump_json())
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
    return StreamingResponse(
        save_after_processing(
            chat_id, messages_to_send, grades_to_send, session, current_chat
        ),
        media_type="application/json",
    )


@matrix_chats_router.post("/{chat_id}/interrupt", response_model=MessageDict)
async def post_interrupt_resolution(
    chat_id: uuid.UUID,
    create_dto: MatrixChatInterruptRequestBase,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> MessageDict:
    chat_service: BaseService[
        MatrixChat, uuid.UUID, Any, UpdateMatrixChatStatusBase
    ] = BaseService(MatrixChat, session)
    response = await run_interrupted(chat_id, create_dto.grade)

    final_classification = response["final_result"]
    await chat_service.update(chat_id, UpdateMatrixChatStatusBase(status="COMPLETED"))
    print(f"CHUNK RESPONSE UPDATED {response}")
    current_chat = await chat_service.get(chat_id)
    user_skill_service: BaseService[UserSkills, int, Any, UpdateUserSkillsRequest] = (
        BaseService(UserSkills, session)
    )
    filters = {
        "user_id": current_chat.user_id,
        "skill_id": current_chat.skill_id,
    }
    user_skill = await user_skill_service.list_all(filters=filters, limit=1, offset=0)
    if len(user_skill) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Skill not found",
        )
    await user_skill_service.update(
        user_skill[0].id,
        UpdateUserSkillsRequest(grade_id=final_classification.final_class_id),
    )
    return MessageDict(
        msg_type="admin_user",
        message=final_classification.message_to_the_user,
        is_execution_blocked=False,
        are_separate_messages=True,
    )


async def get_current_state(thread_id: uuid.UUID) -> StateSnapshot | None:
    async with get_graph() as graph:
        config = {"configurable": {"thread_id": thread_id}}
        current_state = await graph.aget_state(config)
        return current_state


async def save_after_processing(
    thread_id: uuid.UUID,
    msgs: List[MessageDict],
    grades: List[GradeResponseBase],
    session: Annotated[AsyncSession, Depends(get_session)],
    current_chat: MatrixChat,
) -> AsyncGenerator[str, Any]:
    async for chunk in reasoner_run(thread_id, msgs, grades):
        async for processed_chunk in process_chunk(
            thread_id, current_chat, chunk, session
        ):
            yield processed_chunk


async def process_chunk(
    thread_id: uuid.UUID, current_chat: MatrixChat, chunk: str, session: AsyncSession
) -> AsyncGenerator[str, Any]:
    notification_service: BaseService[
        Notification, int, CreateNotificationRequestBase, Any
    ] = BaseService(Notification, session)
    user_skill_service: BaseService[UserSkills, int, Any, UpdateUserSkillsRequest] = (
        BaseService(UserSkills, session)
    )
    chat_service: BaseService[
        MatrixChat, uuid.UUID, Any, UpdateMatrixChatStatusBase
    ] = BaseService(MatrixChat, session)
    response = json.loads(chunk)
    print("CHUNK RESPONSE REASONER -> ", response)
    if response["interrupt_happened"]:
        print(f"INTERRUPT HAPPENED RESPONSE {response}")
        await chat_service.update(
            thread_id, UpdateMatrixChatStatusBase(status="BLOCKED")
        )
        await notification_service.create(
            CreateNotificationRequestBase(
                notification_type="INTERRUPT",
                chat_uuid=thread_id,
                status="UNREAD",
                user_group="ADMIN",
                message=f"Your involvement is required for chat id {thread_id}",
            )
        )
        yield MessageDict(
            msg_type="ai",
            message=response["message"],
            is_execution_blocked=True,
            is_ambiguous=True,
            should_admin_continue=response["should_admin_continue"],
        ).model_dump_json()
    else:
        if (
            "final_result" in response
            and isinstance(response["final_result"], str)
            and response["final_result"] != ""
        ):
            final_classification = FinalClassificationStdOutput.model_validate_json(
                response["final_result"]
            )
            await chat_service.update(
                thread_id, UpdateMatrixChatStatusBase(status="COMPLETED")
            )
            print(f"CHUNK RESPONSE UPDATED {response}")
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
                UpdateUserSkillsRequest(grade_id=final_classification.final_class_id),
            )
    yield MessageDict(
        msg_type="ai",
        message=response["message"],
        should_admin_continue=response["should_admin_continue"],
    ).model_dump_json()
