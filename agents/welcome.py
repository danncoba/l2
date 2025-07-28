import os
import traceback

from typing import Any, List

from dotenv import load_dotenv
from litellm import batch_completion
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from agents.llm_callback import CustomLlmTrackerCallback
from db.models import User, Skill, Grade
from dto.response.matrix_chats import MessageDict
from service.service import BaseService

load_dotenv()

LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LITE_LLM_URL = os.getenv("OPENAI_BASE_URL")
LITE_MODEL = os.getenv("OPENAI_MODEL")


class SingleUserSkillData(BaseModel):
    user_id: int
    skill_id: int


async def prepare_welcome_prompt(
    user_id: int, skill_id: int, session: AsyncSession
) -> List[dict]:
    user_service: BaseService[User, int, Any, Any] = BaseService(User, session)
    skill_service: BaseService[Skill, int, Any, Any] = BaseService(Skill, session)
    grade_service: BaseService[Grade, int, Any, Any] = BaseService(Grade, session)
    grades = await grade_service.list_all()
    user = await user_service.get(user_id)
    skill = await skill_service.get(skill_id)

    prompt_template = ChatPromptTemplate.from_template(
        """
        You need to write a welcoming message to the user in a brief manner, explaining the purpose of the discussion.
        The purpose of the discussion is user self evaluation of specific skill for which grades/expertise level!
        should be selected from user perspective based on available expertise levels (grades).
        Always write the expertise levels/grades available for self-evaluation, their explanations with their values as well!
        Emphasise the expertise we're discussing!Do not sign the message!Make the expertise part of heading!
        Here are the grades available in json format:
        {grades}
        User data in json format:
        {user_json}
        Skill data in json format:
        {skill_json}
        Begin!
        """
    )
    prompt = prompt_template.invoke(
        {
            "grades": grades,
            "user_json": user.model_dump(),
            "skill_json": skill.model_dump(),
        },
    )
    return [{"role": "user", "content": prompt.to_string()}]


async def welcome_agent(user_id: int, skill_id: int, session: AsyncSession):
    prompt = await prepare_welcome_prompt(user_id, skill_id, session)
    model = ChatOpenAI(
        temperature=0,
        base_url=LITE_LLM_URL,
        api_key=LITE_LLM_API_KEY,
        model=LITE_MODEL,
        max_tokens=500,
        streaming=True,
        verbose=True,
        callbacks=[CustomLlmTrackerCallback("welcome")],
    )
    async for chunk in model.astream(prompt):
        message_chunk = MessageDict(
            msg_type="ai", message=chunk.content
        ).model_dump_json()
        yield message_chunk


async def welcome_agent_batch(
    all_requests: List[SingleUserSkillData], session: AsyncSession
) -> List[Any]:
    req_batch = [
        await prepare_welcome_prompt(req.user_id, req.skill_id, session)
        for req in all_requests
    ]
    try:
        responses = batch_completion(
            model=f"azure/{LITE_MODEL}",
            temperature=0,
            max_tokens=400,
            api_key=LITE_LLM_API_KEY,
            api_base=LITE_LLM_URL,
            messages=req_batch,
        )
        return responses
    except Exception as e:
        print(f"Exception type: {type(e)}")
        print(f"Exception message: {str(e)}")
        print(f"Full traceback:")
        traceback.print_exc()
        return []
