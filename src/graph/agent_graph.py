from typing import Annotated
from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

from src.rag.retriever import get_retriever
from src.tools.cmms import TOOLS

OLLAMA_MODEL = "qwen2.5:7b"

retriever = get_retriever()
llm = ChatOllama(model=OLLAMA_MODEL, temperature=0, num_predict=512)
llm_with_tools = llm.bind_tools(TOOLS)


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
    """Need Information? — routing condizionale."""
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(TOOLS))

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "agent")  # dopo il tool, torna all'agent per decidere il prossimo step

    return workflow.compile()


graph = build_graph()