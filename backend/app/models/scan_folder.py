from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ScanFolder(Base):
    __tablename__ = "scan_folders"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(2000), unique=True, nullable=False)
    name = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
