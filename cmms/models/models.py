from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from cmms.database.session import Base


class Machine(Base):
    __tablename__ = "machines"

    id = Column(String, primary_key=True)  # es. "P-102"
    type = Column(String)
    status = Column(String)
    location = Column(String)

    sensor_readings = relationship("SensorReading", back_populates="machine")
    maintenance_events = relationship("MaintenanceEvent", back_populates="machine")
    work_orders = relationship("WorkOrder", back_populates="machine")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(String, primary_key=True)
    machine_id = Column(String, ForeignKey("machines.id"))
    bearing_temp_drive_end_c = Column(Float)
    bearing_temp_non_drive_end_c = Column(Float)
    vibration_rms_mm_s = Column(Float)
    vibration_dominant_freq = Column(String)
    discharge_pressure_bar = Column(Float)
    motor_winding_temp_c = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    machine = relationship("Machine", back_populates="sensor_readings")


class MaintenanceEvent(Base):
    __tablename__ = "maintenance_events"

    id = Column(String, primary_key=True)
    machine_id = Column(String, ForeignKey("machines.id"))
    date = Column(DateTime)
    action = Column(String)
    technician = Column(String)
    result = Column(String, nullable=True)

    machine = relationship("Machine", back_populates="maintenance_events")


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(String, primary_key=True)
    machine_id = Column(String, ForeignKey("machines.id"))
    description = Column(Text)
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)

    machine = relationship("Machine", back_populates="work_orders")