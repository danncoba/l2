from langgraph.prebuilt import create_react_agent
import os
from typing import List, Any, AsyncGenerator, Coroutine

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import StructuredTool, render_text_description
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import Row, RowMapping

from agents.llm_callback import CustomLlmTrackerCallback
from db.db import get_session
from db.models import Grade, UserSkills, User, Skill
from service.service import BaseService
from tools.tools import get_grades_or_expertise

load_dotenv()

LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LITE_LLM_URL = os.getenv("OPENAI_BASE_URL")
LITE_MODEL = os.getenv("OPENAI_MODEL")

custom_callback = CustomLlmTrackerCallback("guidance")

model = ChatOpenAI(
    temperature=0,
    model=LITE_MODEL,
    api_key=LITE_LLM_API_KEY,
    base_url=LITE_LLM_URL,
    streaming=True,
    verbose=True,
    callbacks=[custom_callback],
)


class GuidanceHelperStdOutput(BaseModel):
    has_user_answered: bool = Field(
        description="Whether the user has correctly answered the topic at hand"
    )
    expertise_level: str = Field(
        description="The expertise user has self evaluated himself with"
    )
    expertise_id: int = Field(description="The expertise or grade ID")
    is_more_categories_answered: bool = Field(
        description="if multiple categories have been selected", default=False
    )
    should_admin_be_involved: bool = Field(
        description="Whether the admin should be involved if user is evading the topic or fooling around"
    )
    message: str = Field(description="Message to send to the user")


async def get_current_grade_for_user(
    skill_id: int, user_id: int
) -> None | Row[Any] | RowMapping | Any:
    """
    Useful tool to expertise level or grade for specific skill for a user
    :param skill_id: id of the skill user is looking (ex. Java Development, DevOPS etc...)
    :param user_id: id of the user
    :return: UserSkill explaining the expertise level for specific user and skill
    """
    async for session in get_session():
        service: BaseService[UserSkills, int, Any, Any] = BaseService(
            UserSkills, session
        )
        filters = {
            "skill_id": skill_id,
            "user_id": user_id,
        }
        proper_skill = await service.list_all(filters=filters)
        if len(proper_skill) == 0:
            return None
        return proper_skill[0]


async def provide_guidance(
    msgs: List[str],
    user: User,
    skill: Skill,
) -> AsyncGenerator[GuidanceHelperStdOutput, Any]:
    tools = [
        StructuredTool.from_function(
            function=get_grades_or_expertise,
            coroutine=get_grades_or_expertise,
        ),
        StructuredTool.from_function(
            function=get_current_grade_for_user,
            coroutine=get_current_grade_for_user,
        ),
    ]
    intermediate_steps = []

    system_msg = GUIDANCE_PROMPT
    agent = create_react_agent(model=model, tools=tools)
    async for chunk in agent.astream(
        {
            "messages": [SystemMessage(system_msg)] + msgs,
            "tools": render_text_description(tools),
            "context": msgs[0],
            "intermediate_steps": intermediate_steps,
            "user": user,
            "skill": skill,
        }
    ):
        print("PROVIDE FEEDBACK", chunk)
        content_present = "agent" in chunk and "messages" in chunk["agent"]
        if content_present:
            msg_content = chunk["agent"]["messages"][-1]
            if isinstance(msg_content, AIMessage) and msg_content.content != "":
                content = msg_content.content
                content = content.replace("```json", "").replace("```", "")
                try:
                    ch = GuidanceHelperStdOutput.model_validate_json(content)
                    yield ch
                except ValidationError:
                    yield GuidanceHelperStdOutput(
                        has_user_answered=False,
                        expertise_level="",
                        expertise_id=0,
                        should_admin_be_involved=False,
                        message=content,
                    )
