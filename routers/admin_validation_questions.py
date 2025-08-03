from typing import Annotated, List, Dict
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from db.models import UserValidationQuestions, User
from dto.response.user_validation_questions import (
    UserValidationQuestionResponse,
    AdminValidationQuestionsGroupedResponse,
)
from service.service import BaseService
from security import get_current_user, admin_required
from utils.common import common_parameters

admin_validation_questions_router = APIRouter(
    prefix="/api/v1/admin/validation-questions",
    tags=["Admin Validation Questions"],
    dependencies=[Depends(admin_required)],
)


@admin_validation_questions_router.get(
    "", response_model=List[AdminValidationQuestionsGroupedResponse]
)
async def get_admin_validation_questions(
    session: Annotated[AsyncSession, Depends(get_session)],
    common: Annotated[dict, Depends(common_parameters)],
    current_user: User = Depends(get_current_user),
) -> List[AdminValidationQuestionsGroupedResponse]:
    service = BaseService(UserValidationQuestions, session)
    questions = await service.list_all(
        filters={"status": "waiting_admin"},
        limit=common["limit"],
        offset=common["offset"],
        order_by=[UserValidationQuestions.created_at.asc()],
    )

    user_questions: Dict[int, List[UserValidationQuestionResponse]] = defaultdict(list)
    users_cache = {}

    for question in questions:
        user = await question.awaitable_attrs.user
        skill = await question.awaitable_attrs.skill
        knowledge_base = await question.awaitable_attrs.knowledge_base

        users_cache[user.id] = user
        user_questions[user.id].append(
            UserValidationQuestionResponse(
                **question.model_dump(),
                user=user.model_dump(),
                skill=skill.model_dump(),
                knowledge_base=knowledge_base.model_dump(),
            )
        )

    return [
        AdminValidationQuestionsGroupedResponse(
            user=users_cache[user_id].model_dump(),
            questions=questions_list,
            total_questions=len(questions_list),
        )
        for user_id, questions_list in user_questions.items()
    ]
