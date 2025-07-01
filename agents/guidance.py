from langchain import hub
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import StructuredTool

from db.db import get_session
from db.models import Grade
from dto.response.matrix_chats import MessageDict
import os
from typing import TypedDict, Annotated, Literal, List, Any, AsyncGenerator

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage, SystemMessage
from langgraph.graph.graph import CompiledGraph
from langgraph.types import interrupt, Command
from langgraph.graph import StateGraph, START, END, add_messages
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from service.service import BaseService
from utils.common import convert_msg_dict_to_langgraph_format

load_dotenv()

LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LITE_LLM_URL = os.getenv("OPENAI_BASE_URL")
LITE_MODEL = os.getenv("OPENAI_MODEL")

model = ChatOpenAI(
    model=LITE_MODEL,
    api_key=LITE_LLM_API_KEY,
    base_url=LITE_LLM_URL,
    streaming=True,
    verbose=True,
)


# model = ChatOpenAI(
#     model="gpt-4o",
#     api_key=LITE_LLM_API_KEY,
# )


class AnswerClassification(BaseModel):
    categorization: str = Field(description="classification")
    note: str = Field(description="short additional notes from your observation")


class GuidanceState(TypedDict):
    question: str
    answer: str
    messages: Annotated[list, add_messages]
    classification: str
    irregularity_amount: int


async def prepare_discussion(messages: list[BaseMessage]) -> str:
    discussion = ""
    print(f"Preparing discussion for {messages}")
    for msg in messages:
        if isinstance(msg, AIMessage):
            discussion += f"Question: {msg.content}\n"
        elif isinstance(msg, HumanMessage):
            discussion += f"Answer: {msg.content}\n"
    print(f"Discussion:\n{discussion}")
    return discussion


async def classify_answer(state: GuidanceState) -> GuidanceState:
    prompt_template = ChatPromptTemplate.from_messages(
        (
            "system",
            """
You are classifying discussion (question noted with "Question/Statement:" and answer noted with "Answer:" within pairs) with user to a question to one of the following categories:
direct: answer makes sense and unquestionably answers the question that was asked, without any ambiguity, confusion, evasion, make belief or contradiction
need_help: When user needs additional help with the question or is asking a question related to the question we asked
evasion: When user is evading to answer clearly a question, or when intentionally creating confusion
confusion: When user seems to be confused on the question
unknown: When other categories do not apply

Please prioritize the latest answers than the question and answers from beginning of the discussion!
Answer with the categorization without additional explanation!
Please answer directly to the user!
Original question is the most important question explaining the purpose and intent of the conversation!

Discussion:
{discussion}
        """,
        )
    )
    structured_model = model.with_structured_output(AnswerClassification)
    full_discussion = await prepare_discussion(state["messages"])
    prompt = prompt_template.format(discussion=full_discussion)

    answer = await structured_model.ainvoke(prompt)
    print("CLASSIFY ANSWER ANSWER", answer.categorization)
    msgs = [AIMessage(answer.categorization)]
    if answer.categorization == "direct":
        msgs = []
    return {
        "messages": msgs,
        "classification": answer.categorization,
        "question": None,
        "answer": answer.categorization,
        "irregularity_amount": state["irregularity_amount"],
    }


async def need_help(state: GuidanceState) -> GuidanceState:
    print("NEED HELP")
    prompt_template = ChatPromptTemplate.from_messages(
        (
            "system",
            """
            Provide additional help and explanation to the user explaining the original intent based on the entire
            Discussion.
            Discussion contains Question Answer pairs noted with question "Question/Statement:" and "Answer:"
            Give the user options and possibilities to help him get to the final answer.
            Original question is the most important question explaining the purpose and intent of the conversation!
            Please answer directly to the user!
            Here is the Discussion:
            {discussion}
            """,
        )
    )
    full_discussion = await prepare_discussion(state["messages"])
    prompt = prompt_template.format(discussion=full_discussion)

    answer = await model.ainvoke(prompt)
    print("NEED HELP ANSWER", answer.content)
    return {
        "messages": [AIMessage(answer.content)],
        "classification": state["classification"],
        "question": state["question"],
        "answer": state["answer"],
        "irregularity_amount": state["irregularity_amount"],
    }


async def evasion(state: GuidanceState) -> GuidanceState:
    print("EVASION")
    prompt_template = ChatPromptTemplate.from_messages(
        (
            "system",
            """
        The user is evading the question, providing irrelevant or unrelated answers to the questions based on the discussion.
        Please provide a user with explanation that if continued this will be escalated to managers.
        Original question is the most important question explaining the purpose and intent of the conversation!
        Please answer directly to the user!

        Here is the discussion:
        {discussion}
        """,
        )
    )
    full_discussion = await prepare_discussion(state["messages"])

    prompt = prompt_template.format(discussion=full_discussion)
    answer = await model.ainvoke(prompt)
    print("EVASION ANSWER", answer.content)
    return {
        "messages": [AIMessage(answer.content)],
        "classification": state["classification"],
        "question": state["question"],
        "answer": state["answer"],
        "irregularity_amount": state["irregularity_amount"] + 1,
    }


async def confusion(state: GuidanceState) -> GuidanceState:
    prompt_template = ChatPromptTemplate.from_messages(
        (
            "system",
            """
        The user seems to be confused on the question based on the entire discussion.
        Reiterate the question with additional details explaining better.
        Original question is the most important question explaining the purpose and intent of the conversation!
        Please answer directly to the user!
        Here is the discussion:
        {discussion}
        """,
        )
    )
    full_discussion = await prepare_discussion(state["messages"])
    prompt = prompt_template.format(discussion=full_discussion)
    answer = await model.ainvoke(prompt)
    print("CONFUSION ANSWER", answer.content)
    return {
        "messages": [AIMessage(answer.content)],
        "classification": state["classification"],
        "question": state["question"],
        "answer": state["answer"],
        "irregularity_amount": state["irregularity_amount"] + 1,
    }


async def route_to_individual_helper(
    state: GuidanceState,
) -> Literal["need_help", "evasion", "direct", "confusion"]:
    if state["classification"] == "need_help":
        return "need_help"
    elif state["classification"] == "evasion":
        return "evasion"
    elif state["classification"] == "direct":
        return "direct"
    else:
        return "confusion"


async def finish(state: GuidanceState) -> GuidanceState:
    return state


async def direct(state: GuidanceState) -> GuidanceState:
    return state


async def build_graph() -> CompiledGraph:
    classify_answers = StateGraph(GuidanceState)
    classify_answers.add_node("classify_answer", classify_answer)
    classify_answers.add_node("evasion", evasion)
    classify_answers.add_node("confusion", confusion)
    classify_answers.add_node("need_help", need_help)
    classify_answers.add_node("finish", finish)
    classify_answers.add_node("direct", direct)
    classify_answers.add_edge(START, "classify_answer")
    classify_answers.add_conditional_edges(
        "classify_answer", route_to_individual_helper
    )
    classify_answers.add_edge("need_help", "finish")
    classify_answers.add_edge("evasion", "finish")
    classify_answers.add_edge("confusion", "finish")
    classify_answers.add_edge("direct", END)
    classify_answers.add_edge("finish", END)

    return classify_answers.compile()


async def run_answer_classifier(messages: list[MessageDict]) -> dict:
    graph = await build_graph()
    messages_to_send = convert_msg_dict_to_langgraph_format(messages)
    result = await graph.ainvoke(
        {
            "messages": messages_to_send,
            "classification": "",
        }
    )
    print(result)
    return result


class GuidanceHelperStdOutput(BaseModel):
    has_user_answered: bool = Field(
        description="Whether the user has correctly answered the topic at hand"
    )
    expertise_level: str = Field(
        description="The expertise user has self evaluated himself with"
    )
    expertise_id: int = Field(description="The expertise or grade ID")
    should_admin_be_involved: bool = Field(
        description="Whether the admin should be involved if user is evading the topic or fooling around"
    )
    message: str = Field(description="Message to send to the user")


async def get_grades_or_expertise() -> List[Grade]:
    """
    Useful tool to retrieve current grades or expertise level grading system
    :return: List of json representing those grades and all their fields
    """
    async for session in get_session():
        service: BaseService[Grade, int, Any, Any] = BaseService(Grade, session)
        all_db_grades = await service.list_all()
        all_grades_json: List[str] = []
        for grade in all_db_grades:
            json_grade = grade.model_dump_json()
            all_grades_json.append(json_grade)
        return all_grades_json


async def provide_guidance(
    msgs: List[str],
) -> AsyncGenerator[GuidanceHelperStdOutput, Any]:
    tools = [
        StructuredTool.from_function(
            function=get_grades_or_expertise,
            coroutine=get_grades_or_expertise,
        )
    ]
    intermediate_steps = []

    system_msg = """
    You are helping the user to properly grade their expertise in the mentioned field.
    Everything you help him with should be done by utilizing the tools or around the topic
    of helping him populate his expertise level on the topic.
    Do not discuss anything except from the provided context.
    You are guiding the user to evaluate himself on provided topic.
    Do not discuss anything (any other topic) except from the ones provided in topic!
    Do not chat about other topics with the user, guide him how to populate his expertise with the grades provided
    Warn the user if answering with unrelated topics or evading to answer the question will be escalated by involving managers!
    Topic: {context}
    If the user is evading to answer the question and is not asking any questions related to the topic for 4 or 5 messages
    please involve admin
    When the user answers with proper categorization of skills return only that categorization!
    Format the response in json:
    has_user_answered: bool, description=Whether the user has correctly answered the topic at hand
    expertise_level: str, description=The expertise user has self evaluated himself with
    expertise_id: int, description=The expertise or grade ID
    should_admin_be_involved: bool, description=Whether the admin should be involved if user is evading the topic or fooling around
    message: str, description=Message to send to the user
    """
    agent = create_react_agent(model=model, tools=tools)
    async for chunk in agent.astream(
        {
            "messages": [SystemMessage(system_msg)] + msgs,
            "context": msgs[0],
            "intermediate_steps": intermediate_steps,
        }
    ):
        print("GUIDANCE CHUNK", chunk)
        if "messages" in chunk and isinstance(chunk["messages"][-1], AIMessage):
            if "has_user_answered" in chunk["messages"][-1].content:
                msg_content = chunk["messages"][-1].content
                msg_content = msg_content.replace("```json", "").replace("```", "")
                ch = GuidanceHelperStdOutput.model_validate_json(msg_content)
                yield ch
