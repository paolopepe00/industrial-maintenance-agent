from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.graph.agent_graph import build_graph
from langgraph.checkpoint.memory import MemorySaver

app = FastAPI(title="Industrial Maintenance Agent")

checkpointer = MemorySaver()
graph = build_graph(checkpointer=checkpointer)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    tool_calls: list[str] = []


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}

    result = graph.invoke(
        {"messages": [HumanMessage(content=req.message)]},
        config=config,
    )

    tool_calls_made = [
        f"{m.name}({m.content[:80]})" for m in result["messages"] if isinstance(m, ToolMessage)
    ]

    return ChatResponse(
        answer=result["messages"][-1].content,
        sources=result.get("sources", []),
        tool_calls=tool_calls_made,
    )