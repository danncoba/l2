from typing import List, Any

from db.db import get_session
from db.models import Grade, UserSkills
from dto.response.grades import GradeResponseBase
from service.service import BaseService


async def get_expertise_level_or_grades(query: str) -> List[GradeResponseBase]:
    """Use this tool to get expertise level (grades) from within the system"""
    async for session in get_session():
        service: BaseService[Grade, int, Any, Any] = BaseService(Grade, session)
        return await service.list_all()


async def find_current_grade_for_user_and_skill(
    user_id: int, skill_id: int
) -> UserSkills:
    """
    Utilize to find current expertise and grading level with user id and skill_id
    :param user_id: users id
    :param skill_id: skill id
    :return:
    """
    async for session in get_session():
        user_skill_service: BaseService[UserSkills, int, Any, Any] = BaseService(
            UserSkills, session
        )
        filters = {
            "user_id": user_id,
            "skill_id": skill_id,
        }
        user_skill = await user_skill_service.list_all(filters=filters)
        if len(user_skill) == 0:
            raise Exception(f"No user_skills found for user_id {user_id}")
        single_user_skill = user_skill[0]
        await single_user_skill.awaitable_attrs.user
        await single_user_skill.awaitable_attrs.skill
        await single_user_skill.awaitable_attrs.grade
        return single_user_skill


async def get_grades_or_expertise() -> List[Grade]:
    """
    Useful tool to retrieve current grades or expertise level grading system
    :return: List of json representing those grades and all their fields
    """
    async for session in get_session():
        service: BaseService[Grade, int, Any, Any] = BaseService(Grade, session)
        all_db_grades = await service.list_all()
        all_grades_json: List[str] = []
        for grade in all_db_grades:
            json_grade = grade.model_dump_json()
            all_grades_json.append(json_grade)
        return all_grades_json
