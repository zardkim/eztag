from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class WorkspaceSession(Base):
    """워크스페이스 편집 세션."""
    __tablename__ = "workspace_sessions"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(20), nullable=False, default="editing")
    # editing | applied | moved | discarded
    name = Column(String(200), nullable=True)       # 사용자 지정 이름
    username = Column(String(100), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    applied_at = Column(DateTime(timezone=True), nullable=True)

    items = relationship("WorkspaceItem", back_populates="session", cascade="all, delete-orphan", order_by="WorkspaceItem.sort_order")
    ops = relationship("WorkspaceHistoryOp", back_populates="session", cascade="all, delete-orphan")


class WorkspaceItem(Base):
    """세션에 불러온 개별 파일."""
    __tablename__ = "workspace_items"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("workspace_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    original_tags = Column(JSONB, nullable=True)    # 불러올 당시 태그 스냅샷
    pending_tags = Column(JSONB, nullable=True)     # 변경 예정 태그
    pending_rename = Column(Text, nullable=True)    # 변경 예정 파일명
    status = Column(String(20), nullable=False, default="pending")
    # pending | applied | error | skipped
    apply_error = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    applied_at = Column(DateTime(timezone=True), nullable=True)

    session = relationship("WorkspaceSession", back_populates="items")


class WorkspaceHistoryOp(Base):
    """세션 내 작업 로그."""
    __tablename__ = "workspace_history_ops"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("workspace_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    op_type = Column(String(30), nullable=False)
    # tag_edit | rename | lrc_fetch | cover_change | apply
    op_detail = Column(JSONB, nullable=True)        # 변경 전/후 상세
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("WorkspaceSession", back_populates="ops")
