from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(500), nullable=False, index=True)
    album_artist = Column(String(500), nullable=True)
    year = Column(Integer, nullable=True)
    genre = Column(String(200), nullable=True)
    cover_path = Column(String(1000), nullable=True)
    track_count = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    artist = relationship("Artist", back_populates="albums")
    tracks = relationship("Track", back_populates="album", cascade="all, delete-orphan",
                          order_by="Track.disc_no, Track.track_no")
