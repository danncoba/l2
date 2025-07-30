import os
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator, Any, List, Optional, Literal

from dotenv import load_dotenv
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import RetryPolicy
from langtrace_python_sdk import get_prompt_from_registry
from sqlalchemy.sql.annotation import Annotated
from typing_extensions import TypedDict

from agents.reasoner import get_checkpointer
from dto.request.testing import MessagesRequestBase
from utils.common import convert_msg_request_to_llm_messages

load_dotenv()

LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LITE_LLM_URL = os.getenv("OPENAI_BASE_URL")
LITE_MODEL = os.getenv("OPENAI_MODEL")
LITE_OPENAI_O3_MODEL = os.getenv("LITE_OPENAI_O3_MODEL")

FINAL_ANSWER_STR = "Final Answer: "


class LLMFormatError(Exception):

    def __init__(self, message):
        super().__init__(message)


class LLMChatBuilder:
    def __init__(
        self, model: str, max_tokens: int = 500, stop_sequences: List[str] = None
    ):
        self.model = model
        self.__max_tokens = max_tokens
        self.__stop_sequence = stop_sequences

    def build(self) -> ChatOpenAI:
        if self.model == "gpt-o3-mini":
            return self.__build_gpt_o3_mini()
        return self.__build_gpt_4o()

    def __build_gpt_4o(self) -> ChatOpenAI:
        additional_kw = self.__get_additional_kw()
        model = ChatOpenAI(
            model=LITE_MODEL,
            base_url=LITE_LLM_URL,
            api_key=LITE_LLM_API_KEY,
            temperature=0,
            top_p=1,
            max_tokens=self.__max_tokens,
            stop_sequences=["\nObservation: "],
            # **additional_kw
        )
        return model

    def __build_gpt_o3_mini(self) -> ChatOpenAI:
        additional_kw = self.__get_additional_kw()
        model = ChatOpenAI(
            model=LITE_OPENAI_O3_MODEL,
            base_url=LITE_LLM_URL,
            api_key=LITE_LLM_API_KEY,
            max_tokens=self.__max_tokens,
            temperature=0,
            top_p=1,
            **additional_kw,
        )
        return model

    def __get_additional_kw(self) -> dict[str, str]:
        additional_kw = {}
        if self.__stop_sequence is not None:
            additional_kw["stop_sequences"] = self.__stop_sequence
        return additional_kw


class MatrixValidationState(TypedDict):
    model: str
    question_id: int
    question: str
    answer: str
    rules: Optional[str] = None
    inner_messages: Annotated[list, add_messages]
    guidance_questions: Annotated[list, add_messages]
    messages: Annotated[list, add_messages]
    guidance_amount: int
    next: Annotated[list, add_messages]


@dataclass
class Agent:
    name: str
    description: str
    param: str


def parse_discussion(messages: List[MessagesRequestBase]) -> str:
    full_discussion = ""
    for msg in messages:
        if isinstance(msg, ToolMessage) or isinstance(msg, AIMessage):
            continue
        if msg.role == "ai":
            full_discussion += f"\nQuestion: {msg.message}\n"
        elif msg.role == "human":
            full_discussion += f"\nResponse: {msg.message}\n"

    return full_discussion


async def question_splitter(state: MatrixValidationState) -> MatrixValidationState:
    """
    Define parts of the question that needs to be answered
    by the user. Returns the string representation
    of the required logical units that the answer needs
    to contain from the user to be successfully completed
    :param state:
    :return: the updated state
    :rtype MatrixValidationState
    """
    model = LLMChatBuilder(state["model"]).build()
    prompt_id = "cmdnbhy7c00jjyrs5i348rspq"
    question_definition_prompt = get_prompt_from_registry(prompt_id)
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", question_definition_prompt["value"])]
    )
    user_responses = []
    counter = 0
    for msg in state["messages"]:
        if msg.role == "human":
            counter += 1
            user_responses.append(f"User Answer {counter}: {msg.message}\n")
    print(f"SPLIT -> {state["inner_messages"]}")
    prompt = await prompt_template.ainvoke(
        {
            "question": state["question"],
            "answer": state["answer"],
            "rules": state["rules"],
            "user_responses": "\n".join(user_responses),
        }
    )
    response = await model.ainvoke(prompt)
    return {
        **state,
        "guidance_questions": state.get("guidance_questions", []) + [response],
    }


async def question_validator(state: MatrixValidationState) -> MatrixValidationState:
    """
    Validator that validates and checks that the question
    is not leaking any unnecessary information to the user
    and validates whether the we need to recheck the answer
    :param state:
    :return:
    """
    model = LLMChatBuilder(state["model"]).build()
    prompt_id = "cmdncdcg900jpyrs54a73bh7v"
    question_definition_prompt = get_prompt_from_registry(prompt_id)
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", question_definition_prompt["value"])]
    )
    prompt = await prompt_template.ainvoke(
        {
            "correct_answer": state["answer"],
            "questions": state["guidance_questions"][-1].content,
        }
    )
    response = await model.ainvoke(prompt)
    print(f"RESPONSE GRADING -> {response}")
    match = re.search(r"(Observation:|\nObservation:)", response.content)
    if not match:
        raise LLMFormatError("Invalid response format")
    print(f"FINISHED THIS SETUP -> {response}")
    return {
        **state,
        "inner_messages": state.get("inner_messages", []) + [response],
    }


async def grader(state: MatrixValidationState) -> MatrixValidationState:
    model = LLMChatBuilder(state["model"]).build()
    prompt_id = "cmdnd3zhv00k0yrs5rvseaaeh"
    grader_prompt = get_prompt_from_registry(prompt_id)
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", grader_prompt["value"])]
    )
    user_responses = []
    counter = 0
    for msg in state["messages"]:
        if msg.role == "human":
            counter += 1
            user_responses.append(f"\nUser Answer {counter}: {msg.message}")
    prompt = await prompt_template.ainvoke(
        {
            "grader_prompt": state["answer"],
            "responses": user_responses,
        }
    )
    response = await model.ainvoke(prompt)
    match = re.search(r"(Observation:|\nObservation:)", response.content)
    if not match:
        raise LLMFormatError("Invalid response format")
    return {
        **state,
        "inner_messages": state.get("inner_messages", []) + [response],
    }


async def evaluator(state: MatrixValidationState) -> MatrixValidationState:
    model = LLMChatBuilder(
        state["model"], max_tokens=300, stop_sequences=["\Observation"]
    ).build()
    agents = [
        Agent(
            name="split",
            description="Use this agent when you need clarification what exactly has been answered and what is left unanswered!",
            param="query: The question you want to split",
        ),
        Agent(
            name="grade_user",
            description="Use this agent to grade user responses! Use this grade to return the completeness level.",
            param="User responses",
        ),
    ]
    prompt_id = "cmdnantct00iwyrs5wqoa9nkv"
    grading_prompt = get_prompt_from_registry(prompt_id)
    msgs = convert_msg_request_to_llm_messages(state["messages"])
    discussion = parse_discussion(state["messages"])
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", grading_prompt["value"])]
    )
    print(f"INNER MESSAGES {state['inner_messages']}")
    agents_arr = [
        f"* name: {agent.name}, description: {agent.description}, params: {agent.param}"
        for agent in agents
    ]
    prompt = await prompt_template.ainvoke(
        {
            "agents": "\n".join(agents_arr),
            "agent_names": ",".join([agent.name for agent in agents]),
            "agent_scratchpad": "\n".join(
                [msg.content for msg in state["inner_messages"]]
            ),
            "input": discussion,
        }
    )
    response = await model.ainvoke(prompt)
    next_step = []
    response_msgs = []
    intermediate_msgs = []
    if not FINAL_ANSWER_STR in response.content and not "Action: " in response.content:
        raise LLMFormatError("Not correct response format")
    if FINAL_ANSWER_STR in response.content or response.content.startswith(
        "Final Answer:"
    ):
        next_step.append("finish")
        print(f"FINAL INTERMEDIATE STATE {state["inner_messages"]}")
        if FINAL_ANSWER_STR in response.content:
            response_msgs.append(
                MessagesRequestBase(
                    role="ai",
                    message=response.content.split(FINAL_ANSWER_STR)[1],
                )
            )
        elif response.content.startswith("Final Answer:"):
            response_msgs.append(
                MessagesRequestBase(
                    role="ai", message=response.content.strip("Final Answer: ")
                )
            )
    else:
        if "Action: " in response.content:
            next_step.append("split")
            print(f"APPEND TO INTERMEDIATE STATE {response}")
            intermediate_msgs.append(response)
    return {
        **state,
        "messages": state.get("messages", []) + response_msgs,
        "inner_messages": state.get("inner_messages", []) + intermediate_msgs,
        "next": next_step,
    }


async def reflection_agent(state: MatrixValidationState) -> MatrixValidationState:
    """
    Reflection agent criticizing the work of evaluator agent
    :param state:
    :return:
    """
    model = LLMChatBuilder(
        state["model"], max_tokens=300
    ).build()
    prompt_id = "cmdpiq6g500w8yrs5gop0vctp"
    grading_prompt = get_prompt_from_registry(prompt_id)
    msgs = convert_msg_request_to_llm_messages(state["messages"])
    discussion = parse_discussion(state["messages"])
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", grading_prompt["value"])]
    )
    print(f"INNER MESSAGES {state['inner_messages']}")
    prompt = await prompt_template.ainvoke(
        {
            "question": state["question"],
            "answer": state["answer"],
            "user_responses": state["messages"][-1].message,
        }
    )
    response = await model.ainvoke(prompt)
    msg = MessagesRequestBase(
        role="ai",
        message=response.content,
    )
    return {
        **state,
        "messages": state.get("inner_messages", []) + [msg],
    }



async def finish(state: MatrixValidationState) -> MatrixValidationState:
    return state


async def route_request(
    state: MatrixValidationState,
) -> Literal["finish", "split", "grader"]:
    if len(state["next"]) > 0 and state["next"][-1] == "split":
        return "split"
    if len(state["next"]) > 0 and state["next"][-1] == "grader":
        return "grader"
    return "finish"


@asynccontextmanager
async def get_graph() -> AsyncGenerator[CompiledStateGraph, Any]:
    try:
        async with get_checkpointer() as saver:
            state_graph = StateGraph(MatrixValidationState)
            state_graph.add_node(
                "split",
                question_splitter,
                retry_policy=RetryPolicy(max_attempts=4, initial_interval=2.0),
            )
            state_graph.add_node(
                "evaluator",
                evaluator,
                retry_policy=RetryPolicy(max_attempts=4, initial_interval=2.0),
            )
            state_graph.add_node(
                "validator",
                question_validator,
                retry_policy=RetryPolicy(max_attempts=4, initial_interval=2.0),
            )
            state_graph.add_node(
                "grader",
                grader,
                retry_policy=RetryPolicy(max_attempts=4, initial_interval=2.0),
            )
            state_graph.add_node(
                "reflect",
                reflection_agent,
                retry_policy=RetryPolicy(max_attempts=4, initial_interval=2.0),
            )
            state_graph.add_node(
                "finish",
                finish,
            )
            state_graph.add_edge(START, "evaluator")
            state_graph.add_conditional_edges("evaluator", route_request)
            state_graph.add_edge("split", "validator")
            state_graph.add_edge("validator", "evaluator")
            state_graph.add_edge("grader", "evaluator")
            state_graph.add_edge("finish", END)
            # state_graph.add_edge("finish", "reflect")
            # state_graph.add_edge("reflect", "evaluator")
            state_graph.add_edge("evaluator", END)

            graph = state_graph.compile(checkpointer=saver)
            yield graph
    finally:
        print("Cleaning up")
