import uuid
from datetime import datetime
from cmms.database.session import engine, SessionLocal, Base
from cmms.models.models import Machine, SensorReading, MaintenanceEvent

Base.metadata.create_all(bind=engine)

db = SessionLocal()

if not db.query(Machine).filter_by(id="P-102").first():
    machine = Machine(id="P-102", type="centrifugal_pump", status="running",
                       location="Secondary cooling loop, Building B")
    db.add(machine)

    reading = SensorReading(
        id=str(uuid.uuid4()), machine_id="P-102",
        bearing_temp_drive_end_c=78.5, bearing_temp_non_drive_end_c=71.2,
        vibration_rms_mm_s=6.8, vibration_dominant_freq="2x_running_speed",
        discharge_pressure_bar=4.1, motor_winding_temp_c=118,
        timestamp=datetime.utcnow(),
    )
    db.add(reading)

    db.add(MaintenanceEvent(id=str(uuid.uuid4()), machine_id="P-102",
        date=datetime(2026, 6, 15), action="Bearing re-grease", technician="M. Rossi"))
    db.add(MaintenanceEvent(id=str(uuid.uuid4()), machine_id="P-102",
        date=datetime(2026, 3, 2), action="Laser alignment check", technician="L. Bianchi",
        result="within tolerance"))

    db.commit()
    print("Seed completato.")
else:
    print("P-102 già presente, seed saltato.")

db.close()