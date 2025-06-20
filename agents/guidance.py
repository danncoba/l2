import os
from typing import TypedDict, Annotated, Literal

from dotenv import load_dotenv
from langgraph.graph.graph import CompiledGraph
from langgraph.types import interrupt, Command
from langgraph.graph import StateGraph, START, END, add_messages
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel


load_dotenv()
LITE_LLM_API_KEY = os.getenv("OPENAI_API_KEY")


model = ChatOpenAI(
    model="gpt-4o", api_key=LITE_LLM_API_KEY, streaming=True, verbose=True
)


class GuidanceState(TypedDict):
    question: str
    answer: str
    messages: Annotated[list, add_messages]
    classification: str
    irregularity_amount: int


async def classify_answer(state: GuidanceState) -> GuidanceState:
    prompt_template = ChatPromptTemplate.from_messages(
        (
            "system",
            """
        You are classifying user answers to a question to one of the following categories:
        direct: answer makes sense and answers the question
        need_help: When user needs additional help with the question
        evasion: When user is evading to answer clearly stated question
        confusion: When user seems to be confused on the question
        
        If the answer 
        
        Answer with the categorization without additional explination!
        
        Question: {question}
        Answer: {answer}
        """,
        )
    )
    prompt = prompt_template.format(question=state["question"], answer=state["answer"])

    answer = await model.ainvoke(prompt)

    return {
        "messages": state["messages"],
        "classification": answer.content,
        "question": state["question"],
        "answer": state["answer"],
        "irregularity_amount": 0,
    }


async def need_help(state: GuidanceState) -> GuidanceState:
    prompt_template = ChatPromptTemplate.from_messages(
        (
            "system",
            """
            Provide additional help and explanation to the user explaining the question based on the users answer.
            Give the user options and possibilities to help him get to the final answer.
            Question: {question}
            Answer: {answer}
            """,
        )
    )
    prompt = prompt_template.format(question=state["question"], answer=state["answer"])

    answer = await model.ainvoke(prompt)
    return {
        "messages": [answer.content],
        "classification": state["classification"],
        "question": state["question"],
        "answer": state["answer"],
        "irregularity_amount": state["irregularity_amount"],
    }


async def evasion(state: GuidanceState) -> GuidanceState:
    prompt_template = ChatPromptTemplate.from_messages(
        (
            "system",
            """
        The user is evading the question, providing irrelevant or unrelated answers to the questions.
        Please provide a user with explanation that if continued this will be escalated to managers
        Question: {question}
        Answer: {answer}
        """,
        )
    )
    prompt = prompt_template.format(question=state["question"], answer=state["answer"])
    answer = await model.ainvoke(prompt)
    return {
        "messages": [answer.content],
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
        The user seems to be confused on the question based on users answer.
        Reiterate the question with additional details explaining better
        Question: {question}
        Answer: {answer}
        """,
        )
    )
    prompt = prompt_template.format(question=state["question"], answer=state["answer"])
    answer = await model.ainvoke(prompt)
    print("CONFUSION ANSWER -> ", answer)
    return {
        "messages": [answer.content],
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


async def run_answer_classifier(question: str, answer: str) -> dict:
    graph = await build_graph()
    result = await graph.ainvoke(
        {
            "question": question,
            "answer": answer,
            "messages": [],
            "classification": "",
        }
    )
    print(result)
    return result
