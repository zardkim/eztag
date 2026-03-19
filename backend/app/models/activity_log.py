from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True)
    log_type = Column(String(30), nullable=False)   # tag_write | rename | lrc_search | login | error
    action = Column(String(100), nullable=True)     # 상세 동작 (batch_write, rename_by_tags 등)
    message = Column(Text, nullable=True)           # 요약 메시지
    file_path = Column(Text, nullable=True)         # 대상 파일 경로 (단일/대표)
    username = Column(String(100), nullable=True)   # 요청 사용자
    detail = Column(Text, nullable=True)            # 추가 상세 (JSON 문자열 등)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
