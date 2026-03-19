from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ScanLog(Base):
    __tablename__ = "scan_log"

    id = Column(Integer, primary_key=True)
    scan_type = Column(String(20), nullable=False, default="manual")  # manual / auto / cleanup
    status = Column(String(20), nullable=False, default="running")   # running / success / partial / error
    folder_path = Column(String(2000), nullable=True)
    scanned = Column(Integer, nullable=False, default=0)
    added = Column(Integer, nullable=False, default=0)
    updated = Column(Integer, nullable=False, default=0)
    skipped = Column(Integer, nullable=False, default=0)
    errors = Column(Integer, nullable=False, default=0)
    duration = Column(Float, nullable=False, default=0.0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
