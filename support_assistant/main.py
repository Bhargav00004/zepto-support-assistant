
import os
from typing import TypedDict, List

from fastapi import FastAPI
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END


# ============================================================
# CONFIGURATION
# ============================================================

MOCK_LLM = os.getenv("MOCK_LLM", "1")


# ============================================================
# RESPONSE SCHEMA
# ============================================================

class SupportResponse(BaseModel):
    answer: str
    sources: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


# ============================================================
# GRAPH STATE
# ============================================================

class SupportState(TypedDict, total=False):
    query: str
    intent: str
    retrieved_documents: List[str]
    retrieved_ids: List[str]
    answer: str
    sources: List[str]
    confidence: float


# ============================================================
# INTENT CLASSIFICATION
# ============================================================

def classify_intent(state: SupportState):

    query = state["query"].lower()

    policy_keywords = [
        "delivery",
        "return",
        "refund",
        "membership",
        "tracking",
        "cancel",
        "gift card",
        "support hours"
    ]

    is_policy = any(
        keyword in query
        for keyword in policy_keywords
    )

    if is_policy:
        return {"intent": "policy_question"}

    return {"intent": "general_question"}


# ============================================================
# DIRECT ANSWER
# ============================================================

def direct_answer(state: SupportState):

    response = SupportResponse(
        answer=(
            "I can only answer questions about "
            "Zepto policies right now."
        ),
        sources=[],
        confidence=1.0
    )

    return {
        "answer": response.answer,
        "sources": response.sources,
        "confidence": response.confidence
    }


# ============================================================
# RETRIEVE AND ANSWER
# ============================================================

def retrieve_and_answer(state: SupportState):

    # This is the packaged application version.
    # Retrieval can be connected to the ChromaDB collection
    # created during the notebook stage.

    query = state["query"]

    response = SupportResponse(
        answer=(
            "Please refer to the retrieved Zepto policy "
            "documents for this question."
        ),
        sources=[],
        confidence=0.5
    )

    return {
        "retrieved_documents": [],
        "retrieved_ids": [],
        "answer": response.answer,
        "sources": response.sources,
        "confidence": response.confidence
    }


# ============================================================
# ROUTER
# ============================================================

def route_by_intent(state: SupportState):

    if state["intent"] == "policy_question":
        return "retrieve_and_answer"

    return "direct_answer"


# ============================================================
# LANGGRAPH
# ============================================================

graph_builder = StateGraph(SupportState)

graph_builder.add_node(
    "classify_intent",
    classify_intent
)

graph_builder.add_node(
    "retrieve_and_answer",
    retrieve_and_answer
)

graph_builder.add_node(
    "direct_answer",
    direct_answer
)

graph_builder.add_edge(
    START,
    "classify_intent"
)

graph_builder.add_conditional_edges(
    "classify_intent",
    route_by_intent,
    {
        "retrieve_and_answer": "retrieve_and_answer",
        "direct_answer": "direct_answer"
    }
)

graph_builder.add_edge(
    "retrieve_and_answer",
    END
)

graph_builder.add_edge(
    "direct_answer",
    END
)

support_graph = graph_builder.compile()


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Zepto Support Assistant",
    version="1.0"
)


class AskRequest(BaseModel):
    query: str


class AskResponseModel(BaseModel):
    answer: str
    sources: List[str]
    confidence: float


@app.post(
    "/ask",
    response_model=AskResponseModel
)
def ask(request: AskRequest):

    result = support_graph.invoke(
        {
            "query": request.query
        }
    )

    return AskResponseModel(
        answer=result["answer"],
        sources=result.get("sources", []),
        confidence=result.get("confidence", 1.0)
    )
