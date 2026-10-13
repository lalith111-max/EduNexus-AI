import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Source(Base):
    __tablename__ = "sources"

    id = Column(String(50), primary_key=True, index=True)
    course_id = Column(String(50), ForeignKey("courses.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    source_type = Column(String(50), nullable=False)  # pdf, pptx, notes, audio, video, youtube
    content_hash = Column(String(64), nullable=False, index=True)
    status = Column(String(50), default="pending")  # pending, processing, indexed, error
    error_message = Column(Text, nullable=True)
    extraction_method = Column(String(50), default="text")  # text, ocr, transcript, vision
    page_count = Column(Integer, nullable=True)
    slide_count = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="sources")
    chunks = relationship("Chunk", back_populates="source", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String(80), primary_key=True, index=True)
    course_id = Column(String(50), ForeignKey("courses.id"), nullable=False, index=True)
    source_id = Column(String(50), ForeignKey("sources.id"), nullable=False, index=True)
    source_name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True, index=True)
    slide_number = Column(Integer, nullable=True, index=True)
    timestamp_start = Column(Float, nullable=True)
    timestamp_end = Column(Float, nullable=True)
    heading_path = Column(JSON, default=list)
    concept_tags = Column(JSON, default=list)
    extraction_method = Column(String(50), default="text")
    confidence = Column(Float, default=1.0)
    embedding_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="chunks")
    source = relationship("Source", back_populates="chunks")
