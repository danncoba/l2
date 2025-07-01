import json
import os
import uuid
from contextlib import asynccontextmanager
from typing import TypedDict, Annotated, Optional, Literal, Any, List, AsyncGenerator

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt, Command
from pydantic import BaseModel, Field

from agents.guidance import provide_guidance, GuidanceHelperStdOutput
from agents.llm_callback import CustomLlmTrackerCallback
from db.models import Skill, User
from dto.response.grades import GradeResponseBase
from dto.response.matrix_chats import MessageDict

load_dotenv()
db_url = os.getenv("PG_VECTOR_DATABASE_URL")

LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LITE_LLM_URL = os.getenv("OPENAI_BASE_URL")
LITE_MODEL = os.getenv("OPENAI_MODEL")

model = ChatOpenAI(
    model=LITE_MODEL,
    temperature=0,
    api_key=LITE_LLM_API_KEY,
    base_url=LITE_LLM_URL,
    streaming=True,
    verbose=True,
    callbacks=[CustomLlmTrackerCallback("reasoner")],
)


def multiple_values(a: Any, b: Any) -> Any:
    if a is None and b is not None:
        return b
    elif a is not None and b is None:
        return a
    return b


class AmbiguousStdOutput(BaseModel):
    is_ambiguous: bool
    question: str


class FinalClassificationStdOutput(BaseModel):
    final_class: str = Field(description="Final classification label")
    final_class_id: int = Field(description="Id of the final classification")
    message_to_the_user: str = Field(description="Message to user")


class SpellcheckBase(BaseModel):
    spelling: str
    corrected_spelling: str
    correction_applied: bool


class ReasonerOutputBase(BaseModel):
    classification: str
    classification_explanation: str
    certainty_level: int


class ReasonerState(TypedDict):
    grades: List[GradeResponseBase]
    user: User
    skill: Skill
    messages: Annotated[list, add_messages]
    spellcheck_response: Optional[SpellcheckBase]
    reasoner_response: Optional[ReasonerOutputBase]
    interrupt_state: dict[str, str]
    is_ambiguous: bool
    ambiguous_output: Optional[str]
    should_admin_continue: bool
    number_of_irregularities: Optional[int]
    final_result: Optional[FinalClassificationStdOutput]


class ClassifierState(TypedDict):
    grades: Annotated[List[GradeResponseBase], multiple_values]
    msgs: Annotated[list, add_messages]
    finished_state: Annotated[str, multiple_values]
    interrupt_state: Annotated[dict[str, str], multiple_values]


classifier_builder = StateGraph(ClassifierState)


async def reasoner(state: ClassifierState) -> ClassifierState:
    message = ChatPromptTemplate.from_messages(
        (
            "system",
            """
            Based on the user question you need to categorize into one of the following categories:
            {categories}
            Respond only with the category recognized!
            Response format json:
            classification: str, description=Final classification based on the categories
            classification_explanation: str, description=Final classification explanation (why it was classified in this way)
            certainty_level: int, description=How precise is your classification
            """,
        )
    )
    msg = message.format(categories=state["grades"])
    response = await model.ainvoke(state["msgs"] + [msg])
    msg_output = response.content
    msg_output = msg_output.replace("```json", "").replace("```", "")
    res = ReasonerOutputBase.model_validate_json(msg_output)
    return {
        "msgs": [AIMessage(res.classification)],
        "finished_state": None,
        "grades": state["grades"],
        "interrupt_state": {},
    }


async def reflect(state: ClassifierState) -> ClassifierState:
    input_val = state["msgs"][-2].content
    predicted_state = state["msgs"][-1].content
    prompt_template = ChatPromptTemplate.from_template(
        """
        You are an reviewing user submission categorization of the answer of expertise in a particular subject.
        You are provided the available expertise categories to which you need to categorize into.
        Critique the prediction if you think it's incorrect!
        If you agree with correct prediction respond with exactly "finish" without any explanations!
        If you find the categorization inconclusive or not indicative in any way of the user message respond with exactly "human"!
        Expertise categories:
        {categories}
        Users message: {msg}
        Predicted user expertise: {state}
        """
    )
    prompt = await prompt_template.ainvoke(
        {"state": predicted_state, "msg": input_val, "categories": state["grades"]}
    )
    response = model.invoke(prompt)
    return {
        "msgs": [HumanMessage(response.content)],
        "finished_state": None,
        "grades": state["grades"],
        "interrupt_state": {},
    }


async def correct_found(
    state: ClassifierState,
) -> Literal["reasoner", "human", "finish"]:
    if state["msgs"][-1].content == "finish":
        return "finish"
    elif state["msgs"][-1].content == "human":
        return "human"
    return "reasoner"


async def finish(state: ClassifierState) -> ClassifierState:
    finished_state = state["msgs"][-2].content
    return {
        "msgs": state["msgs"],
        "finished_state": finished_state,
        "grades": state["grades"],
        "interrupt_state": {},
    }


async def human(state: ClassifierState) -> ClassifierState:
    interrupt_val = {
        "answer_to_revisit": state["msgs"][-2].content,
    }
    value = interrupt(
        interrupt_val,
    )
    return {
        "msgs": [AIMessage(value)],
        "finished_state": state["finished_state"],
        "grades": state["grades"],
        "interrupt_state": interrupt_val,
    }


classifier_builder.add_node("reasoner", reasoner)
classifier_builder.add_node("reflect", reflect)
classifier_builder.add_node("finish", finish)
classifier_builder.add_node("human", human)
classifier_builder.add_edge(START, "reasoner")
classifier_builder.add_edge("reasoner", "reflect")
classifier_builder.add_conditional_edges("reflect", correct_found)
classifier_builder.add_edge("reflect", "finish")
classifier_builder.add_edge("human", "finish")
classifier_builder.add_edge("finish", END)

classify = classifier_builder.compile()

builder = StateGraph(ReasonerState)


async def answer_classifier(state: ReasonerState) -> ReasonerState:
    response: GuidanceHelperStdOutput = None
    async for chunk in provide_guidance(state["messages"], state["user"], state["skill"]):
        print("ANSWER CLASSIFIER", chunk)
        if isinstance(chunk, GuidanceHelperStdOutput):
            response = chunk
            print("ACTUAL RETURN")
            return {
                "grades": state["grades"],
                "messages": [AIMessage(response.message)],
                "number_of_irregularities": 0,
                "spellcheck_response": None,
                "reasoner_response": None,
                "interrupt_state": {},
                "is_ambiguous": False,
                "ambiguous_output": (
                    "direct" if response.has_user_answered else "indirect"
                ),
                "user": state["user"],
                "skill": state["skill"],
                "should_admin_continue": response.should_admin_be_involved,
                "final_result": None,
            }

    print("THIS FUCKING RETURN")
    return {
        "grades": state["grades"],
        "messages": [],
        "number_of_irregularities": 0,
        "spellcheck_response": None,
        "reasoner_response": None,
        "interrupt_state": {},
        "is_ambiguous": False,
        "ambiguous_output": None,
        "user": state["user"],
        "skill": state["skill"],
        "should_admin_continue": False,
        "final_result": None,
    }


async def next_step(
    state: ReasonerState,
) -> Literal["deeply_classify", "ask_clarification", "human"]:
    if state["should_admin_continue"]:
        return "human"
    if state["ambiguous_output"] != "direct":
        return "ask_clarification"
    return "deeply_classify"


async def ask_clarification(state: ReasonerState) -> ReasonerState:
    interrupt_val = {
        "answer_to_revisit": state["messages"][-2].content,
    }
    interrupt_msg = interrupt(interrupt_val)
    return {
        "grades": state["grades"],
        "messages": [AIMessage(interrupt_msg)],
        "spellcheck_response": state["spellcheck_response"],
        "reasoner_response": None,
        "interrupt_state": interrupt_val,
        "is_ambiguous": state["is_ambiguous"],
        "ambiguous_output": state["ambiguous_output"],
        "number_of_irregularities": state["number_of_irregularities"],
        "user": state["user"],
        "skill": state["skill"],
        "should_admin_continue": state["should_admin_continue"],
        "final_result": None,
    }


async def deeply_classify(state: ReasonerState) -> ReasonerState:
    async for class_chunk in classify.astream(
        {"msgs": state["messages"], "finished_state": None, "grades": state["grades"]}
    ):
        if (
            "finished_state" in class_chunk
            and class_chunk["finished_state"] is not None
        ):
            msg = class_chunk["finished_state"]

    return {
        "grades": state["grades"],
        "messages": [],
        "spellcheck_response": state["spellcheck_response"],
        "reasoner_response": state["reasoner_response"],
        "interrupt_state": {},
        "is_ambiguous": state["is_ambiguous"],
        "ambiguous_output": state["ambiguous_output"],
        "number_of_irregularities": state["number_of_irregularities"],
        "user": state["user"],
        "skill": state["skill"],
        "should_admin_continue": state["should_admin_continue"],
        "final_result": None,
    }


async def reasoner(state: ReasonerState) -> ReasonerState:
    prompt_template = ChatPromptTemplate.from_template(
        """
        Summarize the conversation and thank the user and show the finalized categorization emphasized!
        Use one of these categories, labels only, do not display the entire object:
        {grades}
        Do not explain yourself and prolong the conversation!
        Respond in json format:
        final_class: str, description=Final classification label
        final_class_id: int, description=Id of the final classification
        message_to_the_user: str, description=Message to user
        """
    )
    prompt = prompt_template.invoke({"grades": state["grades"]})
    response = model.invoke(state["messages"] + [HumanMessage(prompt.to_string())])
    msg = response.content
    msg = msg.replace("```json", "").replace("```", "")
    full_response = FinalClassificationStdOutput.model_validate_json(msg)
    return {
        "grades": state["grades"],
        "messages": [],
        "spellcheck_response": state["spellcheck_response"],
        "reasoner_response": state["reasoner_response"],
        "interrupt_state": {},
        "is_ambiguous": state["is_ambiguous"],
        "ambiguous_output": state["ambiguous_output"],
        "number_of_irregularities": state["number_of_irregularities"],
        "user": state["user"],
        "skill": state["skill"],
        "should_admin_continue": state["should_admin_continue"],
        "final_result": full_response,
    }


async def human(state: ReasonerState) -> ReasonerState:
    interrupt_val = {
        "answer_to_revisit": state["messages"][-2].content,
    }
    value = interrupt(
        interrupt_val,
    )
    return {
        "grades": state["grades"],
        "messages": [value],
        "spellcheck_response": state["spellcheck_response"],
        "reasoner_response": state["reasoner_response"],
        "interrupt_state": {},
        "is_ambiguous": state["is_ambiguous"],
        "ambiguous_output": state["ambiguous_output"],
        "number_of_irregularities": state["number_of_irregularities"],
        "user": state["user"],
        "skill": state["skill"],
        "should_admin_continue": True,
        "final_result": state["final_result"],
    }


builder.add_node("answer_classifier", answer_classifier)
builder.add_node("ask_clarification", ask_clarification)
builder.add_node("deeply_classify", deeply_classify)
builder.add_node("human", human)
builder.add_node("reasoner", reasoner)
builder.add_edge(START, "answer_classifier")
builder.add_conditional_edges("answer_classifier", next_step)
builder.add_edge("ask_clarification", "deeply_classify")
builder.add_edge("deeply_classify", "reasoner")
builder.add_edge("human", "deeply_classify")
builder.add_edge("reasoner", END)

full_graph = builder.compile()


@asynccontextmanager
async def get_checkpointer():
    checkpointer = AsyncPostgresSaver.from_conn_string(db_url)
    # Check if it's a context manager
    if hasattr(checkpointer, "__aenter__"):
        # It's a context manager, use it with async with
        async with checkpointer as checkpointer:
            yield checkpointer
    else:
        # It's the actual checkpointer
        try:
            yield checkpointer
        finally:
            await checkpointer.aclose()


@asynccontextmanager
async def get_graph() -> AsyncGenerator[CompiledStateGraph, Any]:
    async with get_checkpointer() as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)
        yield graph


async def reasoner_run(
    thread_id: uuid.UUID,
    msgs: List[MessageDict],
    grades: List[GradeResponseBase],
    skill: Skill,
    user: User,
) -> AsyncGenerator[str, Any]:
    async with get_graph() as graph:
        config = {"configurable": {"thread_id": thread_id}}
        interrupt_happened = False
        interrupt_value = ""
        processing_type = ""
        message_val = ""
        should_admin_continue = False
        async for chunk in graph.astream(
            {
                "messages": msgs,
                "grades": grades,
                "skill": skill,
                "user": user,
            },
            config,
        ):
            actual_type = list(chunk.keys())[0]

            if actual_type == "answer_classifier":
                processing_type = "Classifying answer"
            elif actual_type == "ambiguity":
                processing_type = "Resolving ambiguity"
            elif actual_type == "__interrupt__":
                processing_type = "Interrupt"
            elif actual_type == "deeply_classify":
                processing_type = "Classifying"
            elif actual_type == "reasoner":
                processing_type = "Finalizing"
            if "__interrupt__" in chunk:
                interrupt_happened = True
                interrupt_value = chunk["__interrupt__"][0].value["answer_to_revisit"]
                message_val = ""
            else:
                should_admin_continue = chunk[actual_type]["should_admin_continue"]
                if "final_result" in chunk[actual_type] is not None:
                    if hasattr(
                        chunk[actual_type]["final_result"], "message_to_the_user"
                    ):
                        message_val = chunk[actual_type][
                            "final_result"
                        ].message_to_the_user
                if len(chunk[actual_type]["messages"]) > 0:
                    message_val = chunk[actual_type]["messages"][-1].content

            yield json.dumps(
                {
                    "type": processing_type,
                    "interrupt_happened": interrupt_happened,
                    "interrupt_value": interrupt_value,
                    "message": message_val,
                    "final_result": (
                        chunk[actual_type]["final_result"].model_dump_json()
                        if "final_result" in chunk[actual_type]
                        and isinstance(
                            chunk[actual_type]["final_result"],
                            FinalClassificationStdOutput,
                        )
                        else ""
                    ),
                    "should_admin_continue": should_admin_continue,
                }
            )


async def run_interrupted(thread_id: uuid.UUID, unblock_value: str) -> dict[str, Any]:
    async with get_graph() as graph:
        config = {"configurable": {"thread_id": thread_id}}
        state = await graph.aget_state(config)
        unblock_response = await graph.ainvoke(
            Command(resume=unblock_value), config=config
        )
        return unblock_response
    return None
