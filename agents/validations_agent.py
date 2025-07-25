import os
import pprint
from contextlib import asynccontextmanager
from typing import TypedDict, AsyncGenerator, Any, List, Optional, Literal

from dotenv import load_dotenv
from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool, render_text_description
from langchain_openai import ChatOpenAI
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import RetryPolicy
from langtrace_python_sdk import get_prompt_from_registry
from sqlalchemy.sql.annotation import Annotated

from agents.reasoner import get_checkpointer
from dto.request.testing import MessagesRequestBase
from tools.tools import get_validator_questions_per_difficulty
from utils.common import convert_msg_request_to_llm_messages

load_dotenv()

LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LITE_LLM_URL = os.getenv("OPENAI_BASE_URL")
LITE_MODEL = os.getenv("OPENAI_MODEL")

FINAL_ANSWER_STR = "Final Answer:"


class LLMFormatError(Exception):

    def __init__(self, message):
        super().__init__(message)


tools = [
    StructuredTool.from_function(
        name="get_validator_questions_per_difficulty",
        func=get_validator_questions_per_difficulty,
        coroutine=get_validator_questions_per_difficulty,
    ),
]


class MatrixValidationState(TypedDict):
    question_id: int
    question: str
    answer: str
    rules: Optional[str] = None
    inner_messages: Annotated[list, add_messages]
    intermediate_steps: Annotated[list, add_messages]
    messages: Annotated[list, add_messages]
    guidance_amount: int


def parse_discussion(messages: List[MessagesRequestBase]) -> str:
    full_discussion = ""
    print(f"MESSAGES {messages}")
    for msg in messages:
        if isinstance(msg, ToolMessage) or isinstance(msg, AIMessage):
            continue
        if msg.role == "ai":
            full_discussion += f"\nQuestion: {msg.message}\n"
        elif msg.role == "human":
            full_discussion += f"\nResponse: {msg.message}\n"

    return full_discussion


async def msg_build(guidance: str) -> str:
    """
    Message Builder for the user. When providing guidance we need
    to construct a message to the user that is quite clear in
    it's needs
    :param guidance: the text that we want to send to the user
    :return: message to the user
    """
    model = ChatOpenAI(
        model=LITE_MODEL,
        base_url=LITE_LLM_URL,
        api_key=LITE_LLM_API_KEY,
        temperature=0,
        max_tokens=500,
    )
    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
        You're helpful assistant providing feedback to the user.
        You will receive a message that needs to be send to the user.
        Your task is to take the message and make a very professional, clear and explainatory
        message that is send to the user!
        Do not sign the message!
        """,
            )
        ]
    )
    prompt = await prompt_template.ainvoke({})
    response = await model.ainvoke(prompt)
    return response.content


async def define_question_parts(state: MatrixValidationState) -> MatrixValidationState:
    """
    Define parts of the question that needs to be answered
    by the user. Returns the string representation
    of the required logical units that the answer needs
    to contain from the user to be successfully completed
    :param state:
    :return: the updated state
    :rtype MatrixValidationState
    """
    model = ChatOpenAI(
        model=LITE_MODEL,
        base_url=LITE_LLM_URL,
        api_key=LITE_LLM_API_KEY,
        temperature=0,
        max_tokens=500,
    )
    prompt_id = "cmde4qsv6009iyrs59mu3utg7"
    question_definition_prompt = get_prompt_from_registry(prompt_id)
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", question_definition_prompt["value"])]
    )
    tools = [
        StructuredTool.from_function(
            name="msg_builder",
            func=msg_build,
            coroutine=msg_build,
        ),
    ]
    prompt = await prompt_template.ainvoke(
        {
            "question": state["question"],
            "answer": state["answer"],
            "rules": state["rules"],
        }
    )
    agent = create_react_agent(model=model, tools=tools)
    response = await agent.ainvoke(prompt)
    pprint.pprint(response, indent=4)
    print(f"MESSAGES QUESTION PARTS {state["messages"]}")
    msg = MessagesRequestBase(
        role="ai",
        message=response["messages"][-1].content
    )
    return {
        "question": state["question"],
        "answer": state["answer"],
        "rules": state["rules"],
        "question_id": state["question_id"],
        "messages": [msg],
        "inner_messages": [response["messages"][-1].content],
        "intermediate_steps": state["intermediate_steps"],
        "guidance_amount": 1
    }


async def grading_agent(state: MatrixValidationState):
    model = ChatOpenAI(
        model=LITE_MODEL,
        base_url=LITE_LLM_URL,
        api_key=LITE_LLM_API_KEY,
        temperature=0,
        max_tokens=300,
    )
    prompt_id = "cmde27c69009eyrs5rg0xgdro"
    grading_prompt = get_prompt_from_registry(prompt_id)
    print(f"STATE MESSAGES : {state["messages"]}")
    msgs = convert_msg_request_to_llm_messages(state["messages"])
    discussion = parse_discussion(state["messages"])
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", grading_prompt["value"])]
    )
    print(f"DISCUSSION {discussion}")
    prompt = await prompt_template.ainvoke(
        {
            "question_id": state["question_id"],
            "tools": render_text_description(tools),
            "tool_names": ",".join([tool.name for tool in tools]),
            "agent_scratchpad": "\n".join(state["intermediate_steps"]),
            "input": discussion,
        }
    )
    agent = create_react_agent(model=model, tools=tools)
    response = await agent.ainvoke(prompt)
    print("RESSSSSSSSSSSS")
    pprint.pprint(response)
    is_valid_response = "messages" in response and len(response["messages"]) > 0
    if (
        not is_valid_response
        or not FINAL_ANSWER_STR in response["messages"][-1].content
    ):
        pprint.pprint(response["messages"][-1])
        raise LLMFormatError("Invalid answer format")
    pprint.pprint(response, indent=4)
    return {
        "question_id": state["question_id"],
        "messages": [response["messages"][-1]],
        "inner_messages": [],
        "intermediate_steps": [],
        "guidance_amount": state["guidance_amount"]
    }


async def finish(state: MatrixValidationState) -> MatrixValidationState:
    return state


async def route_request(state: MatrixValidationState) -> Literal["finish", "split"]:
    if state["guidance_amount"] == 0:
        return "split"
    return "finish"


@asynccontextmanager
async def get_graph() -> AsyncGenerator[CompiledStateGraph, Any]:
    try:
        async with get_checkpointer() as saver:
            state_graph = StateGraph(MatrixValidationState)
            state_graph.add_node(
                "split",
                define_question_parts,
            )
            state_graph.add_node(
                "grading",
                grading_agent,
                retry_policy=RetryPolicy(max_attempts=3),
            )
            state_graph.add_node(
                "finish",
                finish,
            )
            state_graph.add_edge(START, "grading")
            state_graph.add_conditional_edges("grading", route_request)
            state_graph.add_edge("split", "grading")
            state_graph.add_edge("finish", END)
            state_graph.add_edge("grading", END)

            graph = state_graph.compile(checkpointer=saver)
            yield graph
    finally:
        print("Cleaning up")
