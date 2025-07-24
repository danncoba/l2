import asyncio
import json
import os
import pprint
import time

from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import timedelta, date, datetime
from typing import Any, Tuple, Literal, Optional, List, Dict

from billiard.exceptions import WorkerLostError
from celery import shared_task
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langtrace_python_sdk import get_prompt_from_registry, langtrace
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from db.models import (
    Grade,
    Skill,
    MatrixSkillKnowledgeBase,
)
from service.service import BaseService

load_dotenv()

LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LITE_LLM_URL = os.getenv("OPENAI_BASE_URL")
BUILD_MODEL = os.getenv("LITE_OPENAI_O3_MODEL")
BUILDER_PROMPT_ID = (
    "cmd7pckhx0072yrs57rtjn8ld"  # langtrace prompt id to build knowledge base
)

LANGTRACE_API_KEY = os.getenv("LANGTRACE_API_KEY")
LANGTRACE_HOST = os.getenv("LANGTRACE_HOST")

langtrace.init(api_key=LANGTRACE_API_KEY, api_host=LANGTRACE_HOST)

QUESTION_THRESHOLD = 30


class KnowledgeBaseOption(BaseModel):
    option: str
    is_correct: bool


class CreateKnowledgeBaseRequest(BaseModel):
    type: Literal["multi", "single", "input"]
    question: str
    answer: Optional[str] = None
    options: Optional[List[KnowledgeBaseOption]] = None
    is_code: bool


class KnowledgeBaseModelCreate(BaseModel):
    skill_id: int
    difficulty_level: int
    question: str
    answer: Optional[str]
    options: Optional[Any]
    question_type: str
    is_code_question: bool
    rules: str
    created_at: datetime
    updated_at: datetime


@dataclass
class QnABuilder:
    current_question_count: int
    questions_to_create_count: int
    difficulty_level: int


@dataclass
class MatrixBuilderResponse:
    min_value: int
    max_value: int
    q_n_a_builder: Dict[int, List[QnABuilder]]
    skills: Dict[int, str]


def get_start_and_end() -> Tuple[int, int]:
    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=7)
    start_timestamp = int(time.mktime(start.timetuple()))
    end_timestamp = int(time.mktime(end.timetuple()))
    print(f"START {str(start)} END {str(end)}")
    return start_timestamp, end_timestamp


class MatrixValidationResolver(ABC):

    skills: List[Skill] = None

    @abstractmethod
    async def get_min_grade(self) -> int:
        raise NotImplementedError("implement get_min_grade")

    @abstractmethod
    async def get_max_grade(self) -> int:
        raise NotImplementedError("implement get_max_grade")

    @abstractmethod
    async def get_skills(self) -> List[Skill]:
        raise NotImplementedError("implement get_skills")


class MatrixValidationQuestionsResolver(MatrixValidationResolver):

    def __init__(self, session: AsyncSession):
        super().__init__()
        self.__session = session
        self.__grade_service: BaseService[Grade, int, Any, Any] = BaseService(
            Grade, session
        )
        self.__skill_service: BaseService[Skill, int, Any, Any] = BaseService(
            Skill, session
        )
        self.__knowledgebase_service: BaseService[
            MatrixSkillKnowledgeBase, int, KnowledgeBaseModelCreate, Any
        ] = BaseService(MatrixSkillKnowledgeBase, session)
        self.skills = None

    async def get_min_grade(self) -> int:
        statement = text(
            """
            SELECT MIN(value) FROM grades;
            """
        )
        results = await self.__session.execute(statement)
        first = results.first()
        return first[0]

    async def get_max_grade(self) -> int:
        statement = text(
            """
            SELECT MAX(value)
            FROM grades;
            """
        )
        results = await self.__session.execute(statement)
        first = results.first()
        return first[0]

    async def get_skills(self) -> List[Skill]:
        return self.skills

    async def resolve_all_skills(self) -> Dict[int, str]:
        assert self.__skill_service is not None
        self.skills = await self.__skill_service.list_all(limit=100000000, offset=0)
        return await self.__get_skills_ids_and_names()

    async def __get_skills_ids_and_names(self) -> Dict[int, str]:
        skills_ids_and_names = {}
        for item in self.skills:
            skills_ids_and_names[item.id] = item.name
        return skills_ids_and_names

    async def get_qa_count_for_skill(self) -> Dict[int, List[QnABuilder]]:
        statement = text(
            """
            SELECT COUNT(*) as amount, skill_id, difficulty_level
            FROM matrix_skill_knowledgebase 
            GROUP BY skill_id, difficulty_level
            """
        )
        all_grades = await self.__grade_service.list_all(offset=0, limit=100000000)
        results = await self.__session.execute(statement)

        all_res: Dict[int, List[QnABuilder]] = {}
        for result in results:
            qna_builder = QnABuilder(
                current_question_count=result[0],
                questions_to_create_count=QUESTION_THRESHOLD - result[0],
                difficulty_level=result[2],
            )
            try:
                skill_q_n_a_builder = all_res[result[1]]
                skill_q_n_a_builder.append(qna_builder)
                all_res[result[1]] = skill_q_n_a_builder
            except KeyError as e:
                all_res[result[1]] = []
                all_res[result[1]].append(qna_builder)

        for skill in self.skills:
            if skill.id not in all_res:
                all_res[skill.id] = []
                for grade in all_grades:
                    qna_builder = QnABuilder(
                        current_question_count=0,
                        questions_to_create_count=QUESTION_THRESHOLD,
                        difficulty_level=grade.value,
                    )
                    all_res[skill.id].append(qna_builder)

        return all_res

    async def run(self):
        await self.resolve_all_skills()
        all_skills = await self.get_skills()
        current_q_and_a_count_for_skill = await self.get_qa_count_for_skill()
        min_value = await self.get_min_grade()
        max_value = await self.get_max_grade()
        return MatrixBuilderResponse(
            max_value=max_value,
            min_value=min_value,
            q_n_a_builder=current_q_and_a_count_for_skill,
            skills=await self.__get_skills_ids_and_names(),
        )


async def create_matrix_validations():
    async for session in get_session():
        resolver = MatrixValidationQuestionsResolver(session)
        matrix_builder_response = await resolver.run()
        for key in matrix_builder_response.q_n_a_builder.keys():
            for val in matrix_builder_response.q_n_a_builder[key]:
                if val.questions_to_create_count <= 0:
                    continue
                await create_matrix_validation_questions(
                    session,
                    val,
                    key,
                    matrix_builder_response.skills[key],
                    matrix_builder_response.min_value,
                    matrix_builder_response.max_value,
                )


async def create_matrix_validation_questions(
    session: AsyncSession,
    qa_builder: QnABuilder,
    skill_id: int,
    skill_name: str,
    min_grade: int,
    max_grade: int,
):
    knowledgebase_service: BaseService[
        MatrixSkillKnowledgeBase, int, KnowledgeBaseModelCreate, Any
    ] = BaseService(MatrixSkillKnowledgeBase, session)
    model = ChatOpenAI(
        model=BUILD_MODEL,
        base_url=LITE_LLM_URL,
        api_key=LITE_LLM_API_KEY,
    )
    prompt_template_value = get_prompt_from_registry(BUILDER_PROMPT_ID)
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", prompt_template_value["value"])]
    )
    prompt = await prompt_template.ainvoke(
        {
            "scenario_number": qa_builder.questions_to_create_count,
            "min_level": min_grade,
            "max_level": max_grade,
            "topic": skill_name,
            "current_level": qa_builder.difficulty_level,
        }
    )
    response = await model.ainvoke(prompt)
    cnt = response.content
    if cnt.startswith("```json"):
        cnt = cnt.strip("```json").strip("```")
    data = json.loads(cnt)
    knowledge_base = [CreateKnowledgeBaseRequest(**item) for item in data]
    all_dtos: List[KnowledgeBaseModelCreate] = []
    for chunk in knowledge_base:
        all_dtos.append(
            KnowledgeBaseModelCreate(
                skill_id=skill_id,
                difficulty_level=qa_builder.difficulty_level,
                question=chunk.question,
                answer=chunk.answer,
                options=(chunk.options if chunk.options is not None else None),
                question_type=chunk.type,
                rules="Testing",
                is_code_question=chunk.is_code,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        )
    pprint.pprint(f"RESPONSE {cnt}")
    pprint.pprint(f"Knowledgebase: {knowledge_base}")
    created_dtos = await knowledgebase_service.create_many(all_dtos)
    for dto in created_dtos:
        print(f"DTO ---> {dto}")
    return created_dtos


@shared_task
def generate_matrix_validation_questions():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            print("RUNNING LOOP")
            result = loop.run_until_complete(create_matrix_validations())
        # return result
    except RuntimeError as runtime_err:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(create_matrix_validations())
    except WorkerLostError as work_lost_err:
        print(f"Worker lost during task execution: {work_lost_err}")
        # print(f"Task ID: {result.id}")
        # print(f"Task state: {result.state}")
