import os
import re
from collections import Counter
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator, Any, List, Optional, Literal, Tuple

from dotenv import load_dotenv
from langchain_core.messages import (
    ToolMessage,
    AIMessage,
    HumanMessage,
    trim_messages,
    BaseMessage,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import RetryPolicy, interrupt
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

RECURSION_BREAK_STR = """
Observation: All information has been provided. I know the final answer!
"""


class LLMFormatError(Exception):

    def __init__(self, message):
        super().__init__(message)


class LLMChatBuilder:
    """
    Class for building and configuring chat language models.

    This class provides a structured way to create instances of specific chat
    language models with predefined configurations. Users can specify parameters
    such as the model type, maximum token limit, and stop sequences during
    initialization. The class handles the creation of model instances and manages
    specific configurations internally.

    :ivar model: The identifier for the chat language model to be used.
    :type model: str
    :ivar max_tokens: Maximum token config for chat model
    :type max_tokens: int
    :ivar stop_sequences: stop sequences for chat models
    :type stop_sequences: List[str]
    """

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
            **additional_kw,
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


class MsgTrimmer:
    """
    A utility to manage and trim AI and human messages in a structured format.

    This class is designed to streamline the process of handling messages
    based on their roles (either 'ai' or 'human'). It allows for customizing
    trimming behaviors through prompts and calculates message lengths to
    make informed trimming decisions.

    :ivar llm: Instance of LLM built using the provided model string.
    :type llm: name of the openai litellm model
    """

    def __init__(self, model: str):
        self.llm = LLMChatBuilder(model, max_tokens=200).build()
        self.__ai_trimp_prompt_id = "cmdshls0h00xsyrs5f5fdzxkv"
        self.__human_msgs_trim_prompt_id = ""

    def set_ai_trim_prompt_id(self, ai_trim_prompt_id: str):
        self.__ai_trimp_prompt_id = ai_trim_prompt_id

    def set_human_trim_prompt_id(self, human_trim_prompt_id: str):
        self.__human_msgs_trim_prompt_id = human_trim_prompt_id

    def get_ai_trim_prompt(self) -> str:
        return self.__get_langtrace_prompt_with_id(self.__ai_trimp_prompt_id)

    def get_human_trim_prompt(selfs) -> str:
        return self.__get_langtrace_prompt_with_id(self.__human_msgs_trim_prompt_id)

    async def trim(self, messages: List[MessagesRequestBase]) -> List[BaseMessage]:
        len_of_ai_msgs = self.__get_msg_len_for_role(messages, "ai")
        len_of_human_msgs = self.__get_msg_len_for_role(messages, "human")
        if len_of_ai_msgs >= 2:
            return [
                await self.__trim_ai_msgs(messages),
                messages[-1].message,
            ]
        return [messages[-2].message, messages[-1].message]

    def __get_langtrace_prompt_with_id(self, prompt_id: str):
        prompt = get_prompt_from_registry(prompt_id)
        return prompt["value"]

    def __get_msg_len_for_role(
        self, messages: List["MessagesRequestBase"], role: Literal["ai", "human"] = "ai"
    ):
        counter = 0
        for msg in messages:
            if msg.role == role:
                counter += 1
        return counter

    async def __trim_ai_msgs(self, messages: List["MessagesRequestBase"]):
        prompt = self.get_ai_trim_prompt()
        prompt_template = ChatPromptTemplate.from_messages([("system", prompt)])
        prompt = await prompt_template.ainvoke(
            {"messages": "\n- ".join(self.__get_ai_messages(messages))}
        )
        response = await self.llm.ainvoke(prompt)
        return response.content

    def __get_ai_messages(self, messages: List["MessagesRequestBase"]) -> List[str]:
        msgs = []
        for msg in messages:
            if msg.role == "ai":
                msgs.append(msg.message)

        return msgs


class MatrixValidationState(TypedDict):
    model: str
    question_id: int
    question: str
    answer: str
    safety_response: Optional[str] = None
    split_response: Optional[str] = None
    rules: Optional[str] = None
    inner_messages: Annotated[list, add_messages]
    guidance_questions: Annotated[list, add_messages]
    messages: Annotated[list, add_messages]
    guidance_amount: int
    next: Annotated[list, add_messages]
    completed: bool
    final_grade: Literal["Correct", "Incorrect"]
    monitor: Optional[str] = None


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


def has_run_steps(steps: List[str]) -> bool:
    if len(steps) > 0:
        counts = Counter(steps)
        count_of_split = counts["split"]
        if count_of_split > 1:
            return True
    return False


async def start_execution(state: MatrixValidationState) -> MatrixValidationState:
    return state


async def monitor_detector(state: MatrixValidationState) -> MatrixValidationState:
    llm = LLMChatBuilder(
        state["model"], max_tokens=300, stop_sequences=["\nObservation"]
    ).build()
    prompt_id = "cmdu0li9u014syrs5ds86grzz"
    monitor_prompt = get_prompt_from_registry(prompt_id)
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", monitor_prompt["value"]), ("human", state["messages"][-1].message)]
    )
    prompt = await prompt_template.ainvoke({"topic": state["question"]})
    response = await llm.ainvoke(prompt)
    return {"monitor": response.content}


async def evaluator(state: MatrixValidationState) -> MatrixValidationState:
    model = LLMChatBuilder(
        state["model"], max_tokens=300, stop_sequences=["\nObservation"]
    ).build()
    agents = [
        Agent(
            name="split",
            description="Use this agent when you need clarification what exactly has been answered and what is left unanswered!",
            param="query: The question you want to split",
        )
    ]
    prompt_id = "cmdnantct00iwyrs5wqoa9nkv"
    grading_prompt = get_prompt_from_registry(prompt_id)
    trimmer = MsgTrimmer(state["model"])
    msgs = await trimmer.trim(state["messages"])
    msgs = [AIMessage(msgs[0]), HumanMessage(msgs[1])]
    discussion = parse_discussion(state["messages"])
    if has_run_steps(state["next"]):
        msgs.append(
            HumanMessage("Conclude on current information and provide Final Answer")
        )
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", grading_prompt["value"])] + msgs
    )
    guidance = ""
    if state["safety_response"] is not None:
        guidance = f"""
        Here are some instructions you should follow in your response:
        {state["safety_response"]}
        """

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
            "guidance": guidance,
        }
    )
    response = await model.ainvoke(prompt)
    next_step = []
    response_msgs = []
    intermediate_msgs = []
    is_correct_answer = False
    if not FINAL_ANSWER_STR in response.content and not "Action: " in response.content:
        raise LLMFormatError("Not correct response format")
    if FINAL_ANSWER_STR in response.content or response.content.startswith(
        "Final Answer:"
    ):
        next_step.append("finish")
        if FINAL_ANSWER_STR in response.content:
            full_answer = response.content.split(FINAL_ANSWER_STR)[1]
            percentage_match = re.search("Completeness: \d+?%", full_answer)
            if percentage_match:
                full_txt = percentage_match.group()
                full_txt = full_txt.strip("Completeness: ").strip("%")
                if int(full_txt) >= 60:
                    is_correct_answer = True
            response_msgs.append(MessagesRequestBase(role="ai", message=full_answer))
        elif response.content.startswith("Final Answer:"):
            full_answer = response.content.split(FINAL_ANSWER_STR)[1]
            percentage_match = re.search("Completeness: \d+(\.\d+)?%", full_answer)
            if percentage_match:
                full_txt = percentage_match.group()
                full_txt = full_txt.strip("Completeness: ").strip("%")
                if int(full_txt) >= 60:
                    is_correct_answer = True
            response_msgs.append(MessagesRequestBase(role="ai", message=full_answer))
    else:
        if "Action: " in response.content:
            next_step.append("split")
            intermediate_msgs.append(response)
    print("BEFORE EVALUATOR RETURN")
    return {
        "messages": state.get("messages", []) + response_msgs,
        "inner_messages": state.get("inner_messages", []) + intermediate_msgs,
        "next": state.get("next", []) + next_step,
        "completed": is_correct_answer,
        "final_grade": "Correct" if is_correct_answer else "Incorrect",
    }


async def get_question_needs(state: MatrixValidationState) -> MatrixValidationState:
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
    msgs = convert_msg_request_to_llm_messages(state["messages"])
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", question_definition_prompt["value"])] + msgs
    )
    user_responses = []
    counter = 0
    prompt = await prompt_template.ainvoke(
        {
            "question": state["question"],
            "answer": state["answer"],
            "rules": state["rules"],
        }
    )
    response = await model.ainvoke(prompt)
    print("BEFORE SPLIT RETURN")
    if not response.content.startswith("Observation: "):
        raise LLMFormatError("split action invalid response format")
    return {
        "inner_messages": state.get("inner_messages", []) + [response],
    }


async def safety_agent(state: MatrixValidationState) -> MatrixValidationState:
    """

    :param state:
    :return:
    """

    model = LLMChatBuilder(state["model"], max_tokens=300).build()
    prompt_id = "cmdr0133z00wiyrs5ab18a8sy"
    safety_prompt = get_prompt_from_registry(prompt_id)
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", safety_prompt["value"]),
            ("ai", state["question"]),
            ("human", state["answer"]),
        ]
    )
    prompt = await prompt_template.ainvoke({})
    response = await model.ainvoke(prompt)
    print("BEFORE SAFETY RETURN")
    return {
        "safety_response": response.content,
    }


async def finish(state: MatrixValidationState) -> MatrixValidationState:
    msg_updates = []
    if state["completed"] or len(state["messages"]) >= 8:
        interrupt_val = {
            "completed_matrix_validation": state["final_grade"],
        }
        msg_updates.append(interrupt(interrupt_val))
    return {
        "messages": state.get("messages", []) + msg_updates,
    }


async def recursion_check(state: MatrixValidationState) -> MatrixValidationState:
    return {}


async def run_all_checks(state: MatrixValidationState) -> MatrixValidationState:
    return {}


async def break_from_recursion(state: MatrixValidationState) -> MatrixValidationState:
    msgs = [AIMessage(content=RECURSION_BREAK_STR)]
    return {**state, "inner_messages": state.get("inner_messages", []) + msgs}


async def route_request(
    state: MatrixValidationState,
) -> Literal["finish", "recursion_check"]:
    if state["next"][-1] == "split":
        return "recursion_check"
    return "finish"


async def break_loop_decision(
    state: MatrixValidationState,
) -> Literal["break_recursion", "run_checks"]:
    counts = Counter(state["next"])
    count_of_split = counts["split"]
    if len(state["next"]) > 0 and count_of_split > 1:
        return "break_recursion"
    return "run_checks"


@asynccontextmanager
async def get_graph() -> AsyncGenerator[CompiledStateGraph, Any]:
    try:
        async with get_checkpointer() as saver:
            state_graph = StateGraph(MatrixValidationState)
            state_graph.add_node("start_exec", start_execution)
            state_graph.add_node("monitor", monitor_detector)
            state_graph.add_node(
                "evaluator",
                evaluator,
                retry_policy=RetryPolicy(max_attempts=4, initial_interval=1.0),
            )
            state_graph.add_node(
                "split",
                get_question_needs,
                retry_policy=RetryPolicy(max_attempts=4, initial_interval=1.0),
            )
            state_graph.add_node(
                "run_checks",
                run_all_checks,
            )
            state_graph.add_node("recursion_check", recursion_check)
            state_graph.add_node("break_recursion", break_from_recursion)
            state_graph.add_node(
                "safety",
                safety_agent,
                retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0),
            )
            state_graph.add_node(
                "finish",
                finish,
            )
            state_graph.add_edge(START, "start_exec")
            state_graph.add_edge("start_exec", "evaluator")
            state_graph.add_edge("start_exec", "monitor")
            state_graph.add_conditional_edges("evaluator", route_request)
            state_graph.add_conditional_edges("recursion_check", break_loop_decision)
            state_graph.add_edge("break_recursion", "evaluator")
            state_graph.add_edge("run_checks", "split")
            state_graph.add_edge("run_checks", "safety")
            state_graph.add_edge("split", "evaluator")
            state_graph.add_edge("safety", "evaluator")
            state_graph.add_edge("monitor", "finish")
            state_graph.add_edge("evaluator", "finish")
            state_graph.add_edge("finish", END)

            graph = state_graph.compile(checkpointer=saver)
            yield graph
    finally:
        print("Cleaning up")
