import datetime
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Concept(Base):
    __tablename__ = "concepts"

    id = Column(String(50), primary_key=True, index=True)
    course_id = Column(String(50), ForeignKey("courses.id"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    category = Column(String(50), default="core")  # core, formula, algorithm, definition
    topic = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    difficulty_level = Column(String(20), default="intermediate")  # beginner, intermediate, advanced
    source_chunk_ids = Column(JSON, default=list)  # list of chunk_ids
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="concepts")


class PrerequisiteEdge(Base):
    __tablename__ = "prerequisite_edges"

    id = Column(String(50), primary_key=True, index=True)
    course_id = Column(String(50), ForeignKey("courses.id"), nullable=False, index=True)
    prereq_concept_id = Column(String(50), ForeignKey("concepts.id"), nullable=False)
    target_concept_id = Column(String(50), ForeignKey("concepts.id"), nullable=False)
    relationship_type = Column(String(50), default="prerequisite_of")  # prerequisite_of, builds_on
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
