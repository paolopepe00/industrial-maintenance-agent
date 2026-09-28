import uuid
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from cmms.database.session import get_db
from cmms.models.models import Machine, MaintenanceEvent, SensorReading, WorkOrder

app = FastAPI(title="CMMS API")


@app.get("/machines/{machine_id}")
def get_machine(machine_id: str, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter_by(id=machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
    return {"id": machine.id, "type": machine.type, "status": machine.status, "location": machine.location}


@app.get("/machines/{machine_id}/sensors")
def get_sensor_data(machine_id: str, db: Session = Depends(get_db)):
    reading = (
        db.query(SensorReading)
        .filter_by(machine_id=machine_id)
        .order_by(SensorReading.timestamp.desc())
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail=f"No sensor data for {machine_id}")
    return {
        "machine_id": reading.machine_id,
        "bearing_temp_drive_end_C": reading.bearing_temp_drive_end_c,
        "bearing_temp_non_drive_end_C": reading.bearing_temp_non_drive_end_c,
        "vibration_rms_mm_s": reading.vibration_rms_mm_s,
        "vibration_dominant_freq": reading.vibration_dominant_freq,
        "discharge_pressure_bar": reading.discharge_pressure_bar,
        "motor_winding_temp_C": reading.motor_winding_temp_c,
        "timestamp": reading.timestamp.isoformat(),
    }


@app.get("/machines/{machine_id}/maintenance")
def get_maintenance_history(machine_id: str, db: Session = Depends(get_db)):
    events = db.query(MaintenanceEvent).filter_by(machine_id=machine_id).all()
    return {
        "machine_id": machine_id,
        "history": [
            {"date": e.date.strftime("%Y-%m-%d"), "action": e.action,
             "technician": e.technician, "result": e.result}
            for e in events
        ],
    }


@app.get("/work-orders")
def get_open_work_orders(machine_id: str, db: Session = Depends(get_db)):
    orders = db.query(WorkOrder).filter_by(machine_id=machine_id, status="open").all()
    return {
        "machine_id": machine_id,
        "open_work_orders": [
            {"id": o.id, "description": o.description, "created_at": o.created_at.isoformat()}
            for o in orders
        ],
    }


@app.post("/work-orders")
def create_work_order(machine_id: str, description: str, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter_by(id=machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")

    work_order = WorkOrder(
        id=f"WO-{uuid.uuid4().hex[:6].upper()}",
        machine_id=machine_id,
        description=description,
        status="open",
        created_at=datetime.utcnow(),
    )
    db.add(work_order)
    db.commit()
    db.refresh(work_order)

    return {
        "work_order_id": work_order.id,
        "machine_id": work_order.machine_id,
        "description": work_order.description,
        "status": work_order.status,
        "created_at": work_order.created_at.isoformat(),
    }