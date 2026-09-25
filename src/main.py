from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, ToolMessage
from src.graph.agent_graph import build_graph
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
import logging
import time

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("agent")

app = FastAPI(title="Industrial Maintenance Agent")

checkpointer = MemorySaver()
graph = build_graph(checkpointer=checkpointer)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ChatResponse(BaseModel):
    answer: str = ""
    sources: list[str] = []
    tool_calls: list[str] = []
    pending_approval: dict | None = None


class ConfirmRequest(BaseModel):
    thread_id: str
    approve: bool


def _extract_tool_calls(messages):
    return [f"{m.name}({m.content[:80]})" for m in messages if isinstance(m, ToolMessage)]


def _check_pending(config):
    """Se il grafo è fermo prima di write_tools, ritorna i dettagli dell'azione in sospeso."""
    state = graph.get_state(config)
    if state.next and "write_tools" in state.next:
        last_ai = state.values["messages"][-1]
        call = last_ai.tool_calls[0]
        return {
            "tool": call["name"],
            "args": call["args"],
            "tool_call_id": call["id"],
            "reasoning": last_ai.content or "",
        }
    return None


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    start = time.time()
    config = {"configurable": {"thread_id": req.thread_id}}

    logger.info(f"REQUEST thread={req.thread_id} message={req.message!r}")

    try:
        result = graph.invoke({"messages": [HumanMessage(content=req.message)]}, config=config)
    except Exception:
        logger.exception(f"ERROR thread={req.thread_id}")
        raise

    elapsed = time.time() - start
    tool_calls = _extract_tool_calls(result["messages"])

    pending = _check_pending(config)
    if pending:
        logger.info(f"PENDING_APPROVAL thread={req.thread_id} tool={pending['tool']} elapsed={elapsed:.2f}s")
        confirm_prompt = f"Vuoi procedere con: {pending['tool']}({pending['args']})? Conferma su /chat/confirm."
        full_answer = f"{pending['reasoning']}\n\n{confirm_prompt}" if pending["reasoning"] else confirm_prompt
        return ChatResponse(answer=full_answer, tool_calls=tool_calls, pending_approval=pending)

    logger.info(f"RESPONSE thread={req.thread_id} tools={tool_calls} elapsed={elapsed:.2f}s")

    return ChatResponse(
        answer=result["messages"][-1].content,
        sources=result.get("sources", []),
        tool_calls=tool_calls,
    )

@app.post("/chat/confirm", response_model=ChatResponse)
def confirm(req: ConfirmRequest):
    start = time.time()
    config = {"configurable": {"thread_id": req.thread_id}}
    pending = _check_pending(config)

    logger.info(f"CONFIRM_REQUEST thread={req.thread_id} approve={req.approve}")

    if not pending:
        logger.info(f"CONFIRM_NO_PENDING thread={req.thread_id}")
        return ChatResponse(answer="Nessuna azione in sospeso per questo thread.")

    if req.approve:
        result = graph.invoke(None, config=config)  # riprende ed esegue write_tools
    else:
        # Inietta una ToolMessage "finta" che simula il tool come rifiutato,
        # marcandola come prodotta dal nodo write_tools (as_node), poi riprendiamo il grafo
        decline_message = ToolMessage(
            content="User declined this action. Do not retry unless explicitly asked again.",
            tool_call_id=pending["tool_call_id"],
        )
        graph.update_state(config, {"messages": [decline_message]}, as_node="write_tools")
        result = graph.invoke(None, config=config)  # riprende da dopo write_tools → torna su agent

    elapsed = time.time() - start
    tool_calls = _extract_tool_calls(result["messages"])
    logger.info(f"CONFIRM_RESPONSE thread={req.thread_id} approved={req.approve} tools={tool_calls} elapsed={elapsed:.2f}s")

    return ChatResponse(
        answer=result["messages"][-1].content,
        sources=result.get("sources", []),
        tool_calls=tool_calls,
    )