from dto.response.matrix_chats import MessageDict
import os
from typing import TypedDict, Annotated, Literal

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langgraph.graph.graph import CompiledGraph
from langgraph.types import interrupt, Command
from langgraph.graph import StateGraph, START, END, add_messages
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from utils.common import convert_msg_dict_to_langgraph_format

load_dotenv()
LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")


model = ChatOpenAI(
    model="gpt-4o", api_key=LITE_LLM_API_KEY, streaming=True, verbose=True
)


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
