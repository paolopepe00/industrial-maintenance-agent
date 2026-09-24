from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.graph.agent_graph import graph

app = FastAPI(title="Industrial Maintenance Agent")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    tool_calls: list[str] = []


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = graph.invoke({"messages": [HumanMessage(content=req.message)]})

    tool_calls_made = [
        f"{m.name}({m.content[:80]})" for m in result["messages"] if isinstance(m, ToolMessage)
    ]

    return ChatResponse(
        answer=result["messages"][-1].content,
        sources=result.get("sources", []),
        tool_calls=tool_calls_made,
    )