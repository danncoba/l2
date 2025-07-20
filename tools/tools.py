from datetime import date
from typing import List, Any

from db.db import get_session
from db.models import Grade, UserSkills
from dto.response.grades import GradeResponseBase
from service.service import BaseService


async def get_expertise_level_or_grades(query: str) -> List[GradeResponseBase]:
    """
    Use this tool to get expertise level (grades) from within the system
    :param query: string representing the query to search for
    :return list of grades or expertise levels available in the system
    :rtype: List[GradeResponseBase]: List of GradeResponseBase objects
    """
    async for session in get_session():
        service: BaseService[Grade, int, Any, Any] = BaseService(Grade, session)
        return await service.list_all()


async def find_current_grade_for_user_and_skill(
    user_id: int, skill_id: int
) -> UserSkills:
    """
    Utilize to find current expertise and grading level with user id and skill_id
    :param user_id: user id
    :type user_id: int
    :param skill_id: skill id
    :type skill_id: int
    :return: returns user skill grading. If the grade is None that means it's not set up
    :rtype: UserSkills: UserSkills object with all the fields
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
    :rtype: List[Grade]: List of Grade objects
    """
    async for session in get_session():
        service: BaseService[Grade, int, Any, Any] = BaseService(Grade, session)
        all_db_grades = await service.list_all()
        all_grades_json: List[str] = []
        for grade in all_db_grades:
            json_grade = grade.model_dump_json()
            all_grades_json.append(json_grade)
        return all_grades_json


async def get_today_date() -> str:
    """
    Use this tool to retrieve today's date so you can understand how much time has passed
    from the previous evaluation until today
    :return: string representing today's date in format "Today date: %Y-%m-%d"
    :rtype: str
    """
    today = date.today()
    return f"Today date: {today}"


async def get_days_difference(eval_date: date, today_date: date) -> int:
    """
    Calculate the difference in days between two dates.

    This asynchronous function computes the difference in days
    between the provided evaluation date and today's date, given
    as parameters.

    :param eval_date: The evaluation date to compare.
    :param today_date: The current date is used for comparison.
    :return: The difference in days as an integer.
    :rtype int: Number of days since between eval date and today date
    """
    delta = today_date - eval_date
    return delta.days


async def get_validator_questions_per_difficulty(skill_id: int, difficulty_level: int) -> str:
    """
    Retrieve the questions for matrix validation based on skill
    and level of difficulty

    Async function that takes the params of skill and level of difficulty and
    retrieves available questions for that skill and level of difficult

    :param skill_id:
    :param difficulty_level:
    :return: return the questions for validating user experience matrix
    """
    async for session in get_session():
        pass