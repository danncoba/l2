import os
import re
from contextlib import asynccontextmanager
from typing import (
    List,
    Any,
    AsyncGenerator,
    TypedDict,
    Annotated,
    Literal,
)
import operator

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool, render_text_description
from langchain_community.tools import TavilySearchResults
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import interrupt
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END, add_messages
from agents.dto import AgentMessage, ChatMessage

from agents.consts import (
    DISCREPANCY_TEMPLATE,
    SUPERVISOR_TEMPLATE,
    FEEDBACK_TEMPLATE,
    GUIDANCE_TEMPLATE,
)
from agents.llm_callback import CustomLlmTrackerCallback
from agents.reasoner import get_checkpointer
from tools.tools import find_current_grade_for_user_and_skill, get_grades_or_expertise
from utils.common import convert_agent_msg_to_llm_message

load_dotenv()

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
    next_steps: Annotated[List[str], operator.add]
    messages: Annotated[List[AgentMessage], operator.add]
    chat_messages: Annotated[List[ChatMessage], operator.add]


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
    msg = []
    if "messages" in response and len(response["messages"]) > 0:
        response_msgs = response["messages"][-1]
        msg = [
            AgentMessage(
                message=response_msgs,
                role="discrepancy",
            )
        ]
    return {
        "discrepancy": state["discrepancy"],
        "guidance": state["guidance"],
        "next_steps": state["next_steps"],
        "messages": msg,
        "chat_messages": state["chat_messages"],
    }


async def supervisor_agent(state: SupervisorState) -> SupervisorState:
    prompt_template = ChatPromptTemplate.from_template(SUPERVISOR_TEMPLATE)
    msgs = []
    for msg in state["chat_messages"]:
        if msg["role"] == "human":
            answer = f"Answer: {msg["message"]}"
            msgs.append(answer)
        elif msg["role"] == "ai":
            question = f"Question: {msg["message"]}"
            msgs.append(question)
    prompt_msgs = "\n".join(msgs)
    scratchpad_msgs = [m.message.content for m in state["messages"]]
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
    match = re.search(r"\nCall: (discrepancy|guidance|feedback|grading)", content)
    msg_to_append = []
    print(f"SUPERVISOR CHAT MESSAGES -> {state['chat_messages']}")
    if match:
        print("\n\n\nIS MATCHING THIS\n\n\n")
        for val in match.groups():
            next_steps.append(val)
    else:
        next_steps.append("finish")
        chat_msg = ChatMessage(
            message=response,
            role="ai",
        )
        msg_to_append.append(chat_msg)
        print("\n\n\nFINISHHHHHHH\n\n\n")

    msg = AgentMessage(
        message=response,
        role="supervisor",
    )

    return {
        "discrepancy": state["discrepancy"],
        "guidance": state["guidance"],
        "next_steps": next_steps,
        "messages": [msg],
        "chat_messages": msg_to_append,
    }


async def grading_agent(state: SupervisorState) -> SupervisorState:
    system_msg = SystemMessage(
        """
        Based on the provided discussion your job is to confirm the level of expertise of the user!
        If you are not sure that the grade or expertise is clearly recognizable please let the the user know
        If you're certain please state explicitly which expertise is correct for the user!
        """
    )
    model = ChatOpenAI(
        temperature=0,
        max_tokens=50,
        model=LITE_MODEL,
        api_key=LITE_LLM_API_KEY,
        base_url=LITE_LLM_URL,
        streaming=True,
        verbose=True,
    )
    response = await model.ainvoke([system_msg] + state["chat_messages"])
    msg = AgentMessage(message=response, role="grade")
    return {
        "discrepancy": state["discrepancy"],
        "guidance": state["guidance"],
        "next_steps": state["next_steps"],
        "messages": [msg],
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
    model = ChatOpenAI(
        temperature=0,
        max_tokens=300,
        model=LITE_MODEL,
        api_key=LITE_LLM_API_KEY,
        base_url=LITE_LLM_URL,
        streaming=True,
        verbose=True,
    )
    msgs = convert_agent_msg_to_llm_message(state["messages"])
    print(f"\n\nFEEDBACK AGENT PROMPT\n {msgs}")
    print(f"\n\nFEEDBACK AGENT PROMPT\n {state['chat_messages'][-1]}")
    prompt_template = ChatPromptTemplate.from_messages(
        [SystemMessage(FEEDBACK_TEMPLATE)] + msgs
    )
    prompt = await prompt_template.ainvoke(input={})
    feedback_response = await model.ainvoke(prompt)

    interrupt_val = {
        "answer_to_revisit": feedback_response.content,
    }
    print(f"\n\nFEEDBACK AGENT\n {interrupt_val}")
    print(f"\n\nFEEDBACK RESPONSE\n {feedback_response}")
    agent_msg = AgentMessage(
        message=interrupt(
            interrupt_val,
        ),
        role="feedback",
    )
    msg_for_user = ChatMessage(
        message=feedback_response,
        role="ai",
    )

    return {
        "discrepancy": state["discrepancy"],
        "guidance": state["guidance"],
        "next_steps": state["next_steps"],
        "messages": [agent_msg],
        "chat_messages": [msg_for_user],
    }


async def guidance_agent(state: SupervisorState) -> SupervisorState:
    print("\n\n\nENTERING GUIDANCE\n\n\n")
    tools = [search]
    template = ChatPromptTemplate.from_template(GUIDANCE_TEMPLATE)
    prompt = await template.ainvoke(
        input={
            "tools": render_text_description(tools),
            "context": state["chat_messages"][0]["message"],
            "answer": state["chat_messages"][-1]["message"],
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
    msg = AgentMessage(
        message=agent_response["messages"][-1],
        role="guidance",
    )
    return {
        "discrepancy": state["discrepancy"],
        "guidance": state["guidance"],
        "next_steps": state["next_steps"],
        "messages": [msg],
        "chat_messages": state["chat_messages"],
    }


async def finish(state: SupervisorState) -> SupervisorState:
    return state


async def next_step(
    state: SupervisorState,
) -> Literal["guidance", "feedback", "discrepancy", "finish", "grading"]:
    if len(state["next_steps"]) > 0:
        if state["next_steps"][-1] == "guidance":
            return "guidance"
        elif state["next_steps"][-1] == "discrepancy":
            return "discrepancy"
        elif state["next_steps"][-1] == "feedback":
            return "feedback"
        elif state["next_steps"][-1] == "grading":
            return "grading"
    return "finish"


@asynccontextmanager
async def get_graph() -> AsyncGenerator[CompiledStateGraph, Any]:
    try:
        async with get_checkpointer() as saver:
            state_graph = StateGraph(SupervisorState)

            state_graph.add_node("supervisor", supervisor_agent)
            state_graph.add_node("discrepancy", discrepancy_agent)
            state_graph.add_node("guidance", guidance_agent)
            state_graph.add_node("feedback", feedback_agent)
            state_graph.add_node("grading", grading_agent)
            state_graph.add_node("finish", finish)
            state_graph.add_edge(START, "supervisor")
            state_graph.add_conditional_edges("supervisor", next_step)
            state_graph.add_edge("discrepancy", "supervisor")
            state_graph.add_edge("guidance", "supervisor")
            state_graph.add_edge("feedback", "supervisor")
            state_graph.add_edge("grading", "supervisor")
            state_graph.add_edge("finish", END)

            graph = state_graph.compile(checkpointer=saver)
            yield graph
    finally:
        print("Cleaning up")
