import requests
from langchain_core.tools import tool

CMMS_BASE_URL = "http://localhost:8001"


@tool
def get_machine_status(machine_id: str) -> dict:
    """Get current operational status of a machine."""
    resp = requests.get(f"{CMMS_BASE_URL}/machines/{machine_id}")
    if resp.status_code != 200:
        return {"error": resp.json().get("detail", "Unknown error")}
    return resp.json()


@tool
def get_sensor_data(machine_id: str) -> dict:
    """Get latest sensor readings (temperature, vibration, pressure) for a machine."""
    resp = requests.get(f"{CMMS_BASE_URL}/machines/{machine_id}/sensors")
    if resp.status_code != 200:
        return {"error": resp.json().get("detail", "Unknown error")}
    return resp.json()


@tool
def get_maintenance_history(machine_id: str) -> dict:
    """Get recent maintenance events for a machine."""
    resp = requests.get(f"{CMMS_BASE_URL}/machines/{machine_id}/maintenance")
    if resp.status_code != 200:
        return {"error": resp.json().get("detail", "Unknown error")}
    return resp.json()


@tool
def get_open_work_orders(machine_id: str) -> dict:
    """Get currently open work orders for a machine."""
    resp = requests.get(f"{CMMS_BASE_URL}/work-orders", params={"machine_id": machine_id})
    if resp.status_code != 200:
        return {"error": resp.json().get("detail", "Unknown error")}
    return resp.json()


@tool
def create_work_order(machine_id: str, description: str) -> dict:
    """Create a maintenance work order for a machine. Only call this if the user explicitly confirms they want one created."""
    resp = requests.post(
        f"{CMMS_BASE_URL}/work-orders",
        params={"machine_id": machine_id, "description": description},
    )
    if resp.status_code != 200:
        return {"error": resp.json().get("detail", "Unknown error")}
    return resp.json()


TOOLS = [get_machine_status, get_sensor_data, get_maintenance_history,
         get_open_work_orders, create_work_order]