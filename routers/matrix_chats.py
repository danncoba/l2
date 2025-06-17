import uuid
from typing import Annotated, Any, AsyncGenerator, Coroutine, List

from fastapi import APIRouter
from fastapi.params import Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasicCredentials
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from agents.reasoner import reasoner_run, get_graph, run_interrupted
from agents.welcome import welcome_agent
from routers.db.db import get_session
from routers.db.models import Grade, MatrixChat, Notification
from routers.dto.inner.notifications import CreateNotificationRequestBase
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
from security import security

matrix_chats_router = APIRouter(
    prefix="/api/v1/matrix-chats", tags=["Matrix Validations Chat"]
)


async def send_msg_by_msg(msgs: List[MessageDict]):
    for msg in msgs:
        yield msg.model_dump_json()


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
            if len(state.interrupts) > 0:
                messages.append(
                    MessageDict(
                        msg_type="ai",
                        message="Waiting for admin review of this state:"
                        f"**{state.interrupts[0].value["answer_to_revisit"]}**",
                        is_execution_blocked=True,
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
    service: BaseService[Grade, int, Any, Any] = BaseService(Grade, session)
    notification_service: BaseService[
        Notification, int, CreateNotificationRequestBase, Any
    ] = BaseService(Notification, session)
    grades = await service.list_all()
    all_grades = []
    for grade in grades:
        all_grades.append(GradeResponseBase(**grade.model_dump()))
    response = await reasoner_run(chat_id, create_dto.messages, all_grades)
    print("RESPONSE REASONER -> ", response)
    if response["interrupt_happened"]:
        notification_request = CreateNotificationRequestBase(
            notification_type="INTERRUPT",
            user_id=None,
            status="UNREAD",
            chat_uuid=chat_id,
            message="The following message was interrupted",
            user_group="ADMIN",
        )
        await notification_service.create(notification_request)
        return MessageDict(
            msg_type="ai",
            message=f"Finishing the execution. "
            f""
            f"Waiting for admin to confirm the result"
            f"**{response["interrupt_value"]["answer_to_revisit"]}**",
            is_execution_blocked=True,
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
