import operator
import os
import re
from typing import (
    TypedDict,
    Annotated,
    Literal,
)

from dotenv import load_dotenv
from langchain_community.tools import TavilySearchResults
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool, render_text_description
from langchain_openai import ChatOpenAI
from langgraph.graph import add_messages
from langgraph.prebuilt import create_react_agent
from langgraph.types import interrupt
from pydantic import BaseModel

from agents.consts import (
    DISCREPANCY_TEMPLATE,
    SUPERVISOR_TEMPLATE,
    FEEDBACK_TEMPLATE,
    GUIDANCE_TEMPLATE,
)
from agents.guidance import get_grades_or_expertise
from agents.llm_callback import CustomLlmTrackerCallback
from tools.tools import find_current_grade_for_user_and_skill

load_dotenv()

search = TavilySearchResults()

LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LITE_LLM_URL = os.getenv("OPENAI_BASE_URL")
LITE_MODEL = os.getenv("OPENAI_MODEL")

custom_callback = CustomLlmTrackerCallback("guidance")


class DiscrepancyValues(BaseModel):
    grade_id: int
    skill_id: int
    user_id: int


class GuidanceValue(BaseModel):
    messages: Annotated[list, add_messages]


class SupervisorState(TypedDict):
    discrepancy: DiscrepancyValues
    guidance: GuidanceValue
    next_steps: Annotated[list, operator.add]
    messages: Annotated[list, add_messages]
    chat_messages: Annotated[list, add_messages]


async def discrepancy_agent(state: SupervisorState) -> SupervisorState:
    """
    Discrepancy agent that resolves the discrepancies and explains
    the differences between the grades from saved and now provided stated
    :return: None
    """
    discrepancy_callback = CustomLlmTrackerCallback("discrepancy_agent")
    tools = [
        StructuredTool.from_function(
            function=find_current_grade_for_user_and_skill,
            coroutine=find_current_grade_for_user_and_skill,
        ),
        StructuredTool.from_function(
            function=get_grades_or_expertise,
            coroutine=get_grades_or_expertise,
        ),
    ]
    model = ChatOpenAI(
        temperature=0,
        max_tokens=300,
        model=LITE_MODEL,
        api_key=LITE_LLM_API_KEY,
        base_url=LITE_LLM_URL,
        streaming=True,
        verbose=True,
        callbacks=[discrepancy_callback],
    )

    prompt_template = ChatPromptTemplate.from_template(DISCREPANCY_TEMPLATE)
    prompt = await prompt_template.ainvoke(
        input={
            "user_id": state["discrepancy"].user_id,
            "skill_id": state["discrepancy"].skill_id,
            "current_grade": state["discrepancy"].grade_id,
        }
    )
    print(f"\n\nDISCREPANCY AGAIN PROMPT\n {prompt}")
    agent = create_react_agent(model=model, tools=tools)
    response = await agent.ainvoke(prompt)
    print(f"\n\nDISCREPANCY AGAIN RESPONSE\n {response}")
    response_msgs = []
    if "messages" in response and len(response["messages"]) > 0:
        response_msgs = [response["messages"][-1].content]
    return {
        "discrepancy": state["discrepancy"],
        "guidance": state["guidance"],
        "next_steps": state["next_steps"],
        "messages": response_msgs,
        "chat_messages": state["chat_messages"],
    }


async def supervisor_agent(state: SupervisorState) -> SupervisorState:
    """
    Supervisor agent that utilizes different agent to help user get to the goal
    :param state: full supervisor state
    :return: updated supervisor state
    """
    prompt_template = ChatPromptTemplate.from_template(SUPERVISOR_TEMPLATE)
    msgs_len = len(state["chat_messages"])
    msgs = []
    for index in range(0, msgs_len, 2):
        question = f"Question: {state["chat_messages"][index].content}"
        answer = f"Answer: {state["chat_messages"][index + 1].content}"
        msgs.extend([question, answer])
    prompt_msgs = "\n".join(msgs)
    scratchpad_msgs = [m.content for m in state["messages"]]
    scratchpad_msgs_str = "\n".join(scratchpad_msgs)
    prompt = await prompt_template.ainvoke(
        {"discussion": prompt_msgs, "agent_scratchpad": scratchpad_msgs_str}
    )
    print(f"\n\nSUPERVISOR AGENT PROMPT\n {prompt}")

    model = ChatOpenAI(
        temperature=0,
        max_tokens=300,
        model=LITE_MODEL,
        api_key=LITE_LLM_API_KEY,
        base_url=LITE_LLM_URL,
        streaming=True,
        verbose=True,
        stop=["\nObserve:"],
    )
    response = await model.ainvoke(prompt)
    print(f"\n\nSUPERVISOR AGENT RESPONSE\n {response}")
    content = response.content
    next_steps = []
    match = re.search(r"\nCall: (discrepancy|guidance|feedback)", content)

    if match:
        print("\n\n\nIS MATCHING THIS\n\n\n")
        for val in match.groups():
            next_steps.append(val)
    else:
        next_steps.append("finish")
        print("\n\n\nFINISHHHHHHH\n\n\n")

    return {
        "discrepancy": state["discrepancy"],
        "guidance": state["guidance"],
        "next_steps": next_steps,
        "messages": [content],
        "chat_messages": state["chat_messages"],
    }


async def evasion_detector_agent(state: SupervisorState) -> SupervisorState:
    prompt_template = ChatPromptTemplate.from_template(
        """
        From provided discussion, check whether the user is evading to answer a provided question?

        Discussion:
        {}

        Respond in the following format:
        Observe: Your answer
        """
    )
    return state


async def feedback_agent(state: SupervisorState) -> SupervisorState:
    """
    Feedback agent designed to provide user with feedback
    :param state: full supervisor state
    :return: updated supervisor state
    """
    model = ChatOpenAI(
        temperature=0,
        max_tokens=300,
        model=LITE_MODEL,
        api_key=LITE_LLM_API_KEY,
        base_url=LITE_LLM_URL,
        streaming=True,
        verbose=True,
    )
    prompt_template = ChatPromptTemplate.from_messages(
        [SystemMessage(FEEDBACK_TEMPLATE)] + state["messages"]
    )
    prompt = await prompt_template.ainvoke(input={})
    feedback_response = await model.ainvoke(prompt)

    interrupt_val = {
        "answer_to_revisit": "Please provide additional feedback",
    }
    print(f"\n\nFEEDBACK AGENT\n {interrupt_val}")
    print(f"\n\nFEEDBACK RESPONSE\n {feedback_response}")
    value = interrupt(
        interrupt_val,
    )

    return {
        "discrepancy": state["discrepancy"],
        "guidance": state["guidance"],
        "next_steps": state["next_steps"],
        "messages": [interrupt_val],
        "chat_messages": [feedback_response],
    }


async def guidance_agent(state: SupervisorState) -> SupervisorState:
    """
    Guidance agent designed to provide user with guidance answering users questions, unknows
    or doubts
    :param state: full supervisor state
    :return: updated supervisor state
    """
    print("\n\n\nENTERING GUIDANCE\n\n\n")
    tools = [search]
    template = ChatPromptTemplate.from_template(GUIDANCE_TEMPLATE)
    prompt = await template.ainvoke(
        input={
            "tools": render_text_description(tools),
            "context": state["chat_messages"][0].content,
            "answer": state["chat_messages"][-1].content,
        }
    )
    model = ChatOpenAI(
        temperature=0,
        max_tokens=300,
        model=LITE_MODEL,
        api_key=LITE_LLM_API_KEY,
        base_url=LITE_LLM_URL,
        streaming=True,
        verbose=True,
    )
    print(f"\n\nGUIDANCE AGENT PROMPT\n {prompt}")
    agent = create_react_agent(model=model, tools=tools)
    agent_response = await agent.ainvoke(prompt)
    print(f"\n\nGUIDANCE AGENT RESPONSE\n {agent_response}")
    return {
        "discrepancy": state["discrepancy"],
        "guidance": state["guidance"],
        "next_steps": state["next_steps"],
        "messages": [agent_response["messages"][-1]],
        "chat_messages": state["chat_messages"],
    }


async def finish(state: SupervisorState) -> SupervisorState:
    return state


async def next_step(
    state: SupervisorState,
) -> Literal["guidance", "feedback", "discrepancy", "finish"]:
    if len(state["next_steps"]) > 0:
        if state["next_steps"][-1] == "guidance":
            return "guidance"
        elif state["next_steps"][-1] == "discrepancy":
            return "discrepancy"
        elif state["next_steps"][-1] == "feedback":
            return "feedback"
    return "finish"
