from datetime import datetime
import random
from langchain_core.tools import tool

_MACHINES = {
    "P-102": {
        "type": "centrifugal_pump",
        "status": "running",
        "location": "Secondary cooling loop, Building B",
    }
}


@tool
def get_machine_status(machine_id: str) -> dict:
    """Get current operational status of a machine."""
    machine = _MACHINES.get(machine_id)
    if not machine:
        return {"error": f"Machine {machine_id} not found"}
    return {"machine_id": machine_id, **machine}


@tool
def get_sensor_data(machine_id: str) -> dict:
    """Get latest sensor readings (temperature, vibration, pressure) for a machine."""
    if machine_id not in _MACHINES:
        return {"error": f"Machine {machine_id} not found"}
    return {
        "machine_id": machine_id,
        "bearing_temp_drive_end_C": 78.5,
        "bearing_temp_non_drive_end_C": 71.2,
        "vibration_rms_mm_s": 6.8,
        "vibration_dominant_freq": "2x_running_speed",
        "discharge_pressure_bar": 4.1,
        "motor_winding_temp_C": 118,
        "timestamp": datetime.now().isoformat(),
    }


@tool
def get_maintenance_history(machine_id: str) -> dict:
    """Get recent maintenance events for a machine."""
    if machine_id not in _MACHINES:
        return {"error": f"Machine {machine_id} not found"}
    return {
        "machine_id": machine_id,
        "history": [
            {"date": "2026-06-15", "action": "Bearing re-grease", "technician": "M. Rossi"},
            {"date": "2026-03-02", "action": "Laser alignment check", "technician": "L. Bianchi", "result": "within tolerance"},
        ],
    }


@tool
def get_open_work_orders(machine_id: str) -> dict:
    """Get currently open work orders for a machine."""
    if machine_id not in _MACHINES:
        return {"error": f"Machine {machine_id} not found"}
    return {"machine_id": machine_id, "open_work_orders": []}


@tool
def create_work_order(machine_id: str, description: str) -> dict:
    """Create a maintenance work order for a machine. Only call this if the user explicitly confirms they want one created."""
    if machine_id not in _MACHINES:
        return {"error": f"Machine {machine_id} not found"}
    work_order_id = f"WO-{random.randint(1000, 9999)}"
    return {
        "work_order_id": work_order_id,
        "machine_id": machine_id,
        "description": description,
        "status": "open",
        "created_at": datetime.now().isoformat(),
    }


TOOLS = [get_machine_status, get_sensor_data, get_maintenance_history,
         get_open_work_orders, create_work_order]