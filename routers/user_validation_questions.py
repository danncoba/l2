import uuid
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends
from langchain_core.messages import AIMessage
from sqlalchemy.ext.asyncio import AsyncSession

from agents.validations_agent import get_graph
from db.db import get_session
from db.models import UserValidationQuestions, MatrixSkillKnowledgeBase, User
from dto.request.testing import MessagesRequestBase
from dto.request.user_validation_questions import (
    MultiOptionQuestionRequest,
    SingleOptionQuestionRequest,
    AnswerInputQuestionRequest,
)
from dto.response.user_validation_questions import (
    UserValidationQuestionResponse,
    KnowledgeBaseQuestionResponse,
    UserKnowledgeBaseResponse,
)
from service.service import BaseService
from security import get_current_user
from utils.common import common_parameters

user_validation_questions_router = APIRouter(
    prefix="/api/v1/user/validation-questions",
    tags=["User Validation Questions"],
)


FINAL_ANSWER = "Final Answer: "


@user_validation_questions_router.get(
    "", response_model=List[UserValidationQuestionResponse]
)
async def get_user_validation_questions(
    session: Annotated[AsyncSession, Depends(get_session)],
    common: Annotated[dict, Depends(common_parameters)],
    current_user: User = Depends(get_current_user),
) -> List[UserValidationQuestionResponse]:
    service = BaseService(UserValidationQuestions, session)
    questions = await service.list_all(
        filters={"user_id": current_user.id},
        limit=common["limit"],
        offset=common["offset"],
    )
    user, skill, knowledge_base = None, None, None
    full_questions = []
    for question in questions:
        user = await question.awaitable_attrs.user
        skill = await question.awaitable_attrs.skill
        knowledge_base = await question.awaitable_attrs.knowledge_base
        full_questions.append(
            UserValidationQuestionResponse(
                **question.model_dump(),
                user=user.model_dump(),
                skill=skill.model_dump(),
                knowledge_base=knowledge_base.model_dump(),
            )
        )

        print(f"QUESTION -> {question}")

    return full_questions


@user_validation_questions_router.get(
    "/{question_id}/knowledge-base", response_model=KnowledgeBaseQuestionResponse
)
async def get_knowledge_base_question(
    question_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KnowledgeBaseQuestionResponse:
    validation_service = BaseService(UserValidationQuestions, session)
    knowledge_service = BaseService(MatrixSkillKnowledgeBase, session)

    try:
        # Get user validation question and verify ownership
        user_question = await validation_service.get(question_id)
        if user_question.user_id != current_user.id:
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Access denied")

        knowledge_question = await knowledge_service.get(
            user_question.knowledge_base_id
        )
        response_data = knowledge_question.model_dump()
        if knowledge_question.question_type == "input":
            response_data["answer"] = None
        if knowledge_question.question_type in [
            "multi",
            "single",
        ] and response_data.get("options"):
            response_data["options"] = [
                {"option": opt.get("option")} for opt in response_data["options"]
            ]

        return KnowledgeBaseQuestionResponse(**response_data)
    except Exception as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Question not found: {str(e)}")


@user_validation_questions_router.post(
    "/{question_id}/answer/multi",
)
async def answer_multi_validation_question(
    question_id: int,
    dto: MultiOptionQuestionRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    pass


@user_validation_questions_router.post(
    "/{question_id}/answer/single",
)
async def answer_single_validation_question(
    question_id: int,
    dto: SingleOptionQuestionRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    pass


@user_validation_questions_router.post(
    "/{question_id}/answer/input", response_model=MessagesRequestBase
)
async def answer_input_validation_question(
    question_id: int,
    dto: AnswerInputQuestionRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MessagesRequestBase:
    async for session in get_session():
        service = BaseService(UserValidationQuestions, session)
        question = await service.get(question_id)
        skill = await question.awaitable_attrs.skill
        knowledge_base = await question.awaitable_attrs.knowledge_base
        async with get_graph() as graph:
            configurable_run = {
                "configurable": {"thread_id": uuid.uuid4()},
                "recursion_limit": 10,
            }
            response = await graph.ainvoke(
                {
                    "question_id": knowledge_base.id,
                    "messages": dto.messages,
                    "inner_messages": [],
                    "intermediate_steps": [],
                },
                configurable_run,
            )
            msg = response["messages"][-1]
            answer = msg.content
            actual_answer_index = answer.index(FINAL_ANSWER) + len(FINAL_ANSWER)
            actual_answer = answer[actual_answer_index:]
            if isinstance(msg, AIMessage):
                return MessagesRequestBase(role="ai", message=actual_answer)
            else:
                return MessagesRequestBase(role="human", message=actual_answer)
