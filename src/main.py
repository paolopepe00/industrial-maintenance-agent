from fastapi import FastAPI
from pydantic import BaseModel
import ollama
import json
from src.rag.retriever import get_retriever
from src.tools import cmms

app = FastAPI(title="Industrial Maintenance Agent")

OLLAMA_MODEL = "qwen2.5:7b"
retriever = get_retriever()

AVAILABLE_TOOLS = {
    "get_machine_status": cmms.get_machine_status,
    "get_sensor_data": cmms.get_sensor_data,
    "get_maintenance_history": cmms.get_maintenance_history,
    "get_open_work_orders": cmms.get_open_work_orders,
    "create_work_order": cmms.create_work_order,
}

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "get_machine_status",
        "description": "Get current operational status of a machine",
        "parameters": {"type": "object", "properties": {
            "machine_id": {"type": "string", "description": "Machine ID, e.g. P-102"}},
            "required": ["machine_id"]},
    }},
    {"type": "function", "function": {
        "name": "get_sensor_data",
        "description": "Get latest sensor readings (temperature, vibration, pressure) for a machine",
        "parameters": {"type": "object", "properties": {
            "machine_id": {"type": "string", "description": "Machine ID, e.g. P-102"}},
            "required": ["machine_id"]},
    }},
    {"type": "function", "function": {
        "name": "get_maintenance_history",
        "description": "Get recent maintenance events for a machine",
        "parameters": {"type": "object", "properties": {
            "machine_id": {"type": "string", "description": "Machine ID, e.g. P-102"}},
            "required": ["machine_id"]},
    }},
    {"type": "function", "function": {
        "name": "get_open_work_orders",
        "description": "Get currently open work orders for a machine",
        "parameters": {"type": "object", "properties": {
            "machine_id": {"type": "string", "description": "Machine ID, e.g. P-102"}},
            "required": ["machine_id"]},
    }},
    {"type": "function", "function": {
        "name": "create_work_order",
        "description": "Create a maintenance work order for a machine. Only call this if the user explicitly confirms they want one created.",
        "parameters": {"type": "object", "properties": {
            "machine_id": {"type": "string", "description": "Machine ID, e.g. P-102"},
            "description": {"type": "string", "description": "Description of the issue"}},
            "required": ["machine_id", "description"]},
    }},
]


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    tool_calls: list[str] = []


def retrieve_context(query: str):
    docs = retriever.invoke(query)
    context = "\n\n".join(d.page_content for d in docs)
    sources = list({d.metadata.get("source", "unknown") for d in docs})
    return context, sources


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    context, sources = retrieve_context(req.message)

    system_prompt = f"""You are an industrial maintenance assistant.
Use the available tools to fetch live machine data (status, sensors, maintenance history, work orders) when needed.
Use the following documentation as reference when relevant:

{context}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": req.message},
    ]

    tool_calls_made = []

    response = ollama.chat(model=OLLAMA_MODEL, messages=messages, tools=TOOL_SCHEMAS)
    messages.append(response["message"])

    # Tool-calling loop: keep resolving tool calls until the model gives a final answer
    while response["message"].get("tool_calls"):
        for call in response["message"]["tool_calls"]:
            name = call["function"]["name"]
            args = call["function"]["arguments"]
            tool_calls_made.append(f"{name}({args})")

            result = AVAILABLE_TOOLS[name](**args)

            messages.append({
                "role": "tool",
                "content": json.dumps(result),
            })

        response = ollama.chat(model=OLLAMA_MODEL, messages=messages, tools=TOOL_SCHEMAS)
        messages.append(response["message"])

    return ChatResponse(
        answer=response["message"]["content"],
        sources=sources,
        tool_calls=tool_calls_made,
    )