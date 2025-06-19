import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, Skill, Grade
from dto.response.matrix_chats import MessageDict
from service.service import BaseService

load_dotenv()


LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
print("LLM API KEY: ", LITE_LLM_API_KEY)
# LITE_LLM_URL = os.getenv("OPENAI_BASE_URL")
# LITE_MODEL = os.getenv("OPENAI_MODEL")

# model = ChatOpenAI(
#     base_url=LITE_LLM_URL, api_key=LITE_LLM_API_KEY, model=LITE_MODEL, streaming=True
# )
model = ChatOpenAI(model="gpt-4o", api_key=LITE_LLM_API_KEY, streaming=True)


async def welcome_agent(user_id: int, skill_id: int, session: AsyncSession):
    user_service: BaseService[User, int, Any, Any] = BaseService(User, session)
    skill_service: BaseService[Skill, int, Any, Any] = BaseService(Skill, session)
    grade_service: BaseService[Grade, int, Any, Any] = BaseService(Grade, session)
    grades = await grade_service.list_all()
    user = await user_service.get(user_id)
    skill = await skill_service.get(skill_id)

    prompt_template = ChatPromptTemplate.from_template(
        """
        You need to write a welcoming message to the user in a brief manner, explaining the purpose of the discussion.
        The purpose of the discussion explain the user and try to make them understand what expertise
        should be selected from user perspective based on available expertise levels (grades).
        Emphasise the expertise we're discussing!Do not sign the message!Make the expertise part of heading!
        Here are the grades available in json format:
        {grades}
        User data in json format:
        {user_json}
        Skill skill in json format:
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
    async for chunk in model.astream(prompt):
        message_chunk = MessageDict(
            msg_type="ai", message=chunk.content
        ).model_dump_json()
        yield message_chunk
