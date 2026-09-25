from typing import Annotated
from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

from src.rag.retriever import get_retriever

from src.tools.cmms import (
    get_machine_status, get_sensor_data, get_maintenance_history,
    get_open_work_orders, create_work_order,
)

OLLAMA_MODEL = "qwen2.5:7b"

retriever = get_retriever()
import os
llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
    temperature=0,
    num_predict=512,
)

READ_TOOLS = [get_machine_status, get_sensor_data, get_maintenance_history, get_open_work_orders]
WRITE_TOOLS = [create_work_order]
ALL_TOOLS = READ_TOOLS + WRITE_TOOLS
WRITE_TOOL_NAMES = {t.name for t in WRITE_TOOLS}

llm_with_tools = llm.bind_tools(ALL_TOOLS)


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    context: NotRequired[str]
    sources: NotRequired[list[str]]


def retrieve_node(state: AgentState) -> dict:
    """Analyze Query + RAG lookup, in un solo nodo."""
    query = state["messages"][-1].content
    docs = retriever.invoke(query)
    context = "\n\n".join(d.page_content for d in docs)
    sources = list({d.metadata.get("source", "unknown") for d in docs})
    return {"context": context, "sources": sources}


def agent_node(state: AgentState) -> dict:
    """Decide se rispondere direttamente o chiamare un tool."""
    system_msg = SystemMessage(content=f"""You are an industrial maintenance assistant.

Rules:
- Before calling a tool, check the conversation history: if you already have that data, do NOT call the same tool with the same arguments again.
- When reasoning about vibration, match the frequency EXACTLY to the documentation below — do not guess or use general knowledge instead of the provided text.
- Give a precise, evidence-based diagnosis citing the specific values you retrieved (e.g. "vibration is X mm/s at Y", not vague statements).
- Only propose a work order after you have a clear diagnosis, not before.

Reference documentation:
{state['context']}""")

    response = llm_with_tools.invoke([system_msg] + state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    """Need Information? — routing condizionale, distingue lettura da scrittura."""
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", None)
    if not tool_calls:
        return END
    if any(call["name"] in WRITE_TOOL_NAMES for call in tool_calls):
        return "write_tools"
    return "read_tools"


def build_graph(checkpointer=None):
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("read_tools", ToolNode(READ_TOOLS))
    workflow.add_node("write_tools", ToolNode(WRITE_TOOLS))

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "agent")
    workflow.add_conditional_edges(
        "agent", should_continue,
        {"read_tools": "read_tools", "write_tools": "write_tools", END: END},
    )
    workflow.add_edge("read_tools", "agent")
    workflow.add_edge("write_tools", "agent")

    return workflow.compile(checkpointer=checkpointer, interrupt_before=["write_tools"])


graph = build_graph()