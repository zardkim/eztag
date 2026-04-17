from sqlalchemy import Column, Integer, String, Float, BigInteger, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    album_id = Column(Integer, ForeignKey("albums.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(500), nullable=False, index=True)
    artist = Column(String(500), nullable=True, index=True)
    album_artist = Column(String(500), nullable=True)
    album_title = Column(String(500), nullable=True)
    track_no = Column(Integer, nullable=True)
    total_tracks = Column(Integer, nullable=True)
    disc_no = Column(Integer, nullable=True, default=1)
    year = Column(Integer, nullable=True)
    release_date = Column(String(20), nullable=True)
    genre = Column(String(200), nullable=True)
    label = Column(String(200), nullable=True)
    isrc = Column(String(20), nullable=True)
    duration = Column(Float, nullable=True)       # seconds
    bitrate = Column(Integer, nullable=True)      # kbps
    sample_rate = Column(Integer, nullable=True)  # Hz
    tag_version = Column(String(20), nullable=True)  # e.g. ID3v2.3, Vorbis
    comment = Column(Text, nullable=True)
    file_path = Column(String(2000), unique=True, nullable=False, index=True)
    file_format = Column(String(10), nullable=True)   # mp3/flac/m4a/ogg
    file_size = Column(BigInteger, nullable=True)
    modified_time = Column(Float, nullable=True)
    lyrics = Column(Text, nullable=True)
    has_cover = Column(Boolean, default=False)
    has_lyrics = Column(Boolean, default=False)
    is_title_track = Column(Boolean, default=False, nullable=True)  # 타이틀곡 여부 (DB 전용)
    youtube_url = Column(String(500), nullable=True)                # 뮤직비디오 YouTube URL (DB 전용)
    auto_tag_status = Column(String(20), nullable=True)             # 파일명 자동태그 결과: ok | no_match | null
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    album = relationship("Album", back_populates="tracks")
