from sqlalchemy import Column, Integer, String, Text, ForeignKey, UniqueConstraint
from app.database import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_user_pref"),)
