import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(String(50), primary_key=True, index=True)
    course_id = Column(String(50), ForeignKey("courses.id"), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    concept_id = Column(String(50), nullable=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(30), nullable=False)  # mcq, short_answer, numerical
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    options_json = Column(JSON, nullable=True)  # list of strings for MCQ
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    rubric = Column(Text, nullable=True)
    formula = Column(String(255), nullable=True)  # for numerical calculation
    tolerance = Column(Float, default=0.01)       # for numerical tolerance
    source_ids = Column(JSON, default=list)       # list of source_ids
    chunk_ids = Column(JSON, default=list)        # list of chunk_ids
    citations = Column(JSON, default=list)        # list of citation objects
    is_verified = Column(Boolean, default=True)
    validation_status = Column(String(50), default="valid")  # valid, flagged, rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String(50), primary_key=True, index=True)
    course_id = Column(String(50), ForeignKey("courses.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    mode = Column(String(30), default="practice")  # practice, exam, diagnostic
    topic = Column(String(100), nullable=True)
    time_limit_mins = Column(Integer, default=15)
    questions_json = Column(JSON, default=list)  # list of Question objects/IDs
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="assessments")
    attempts = relationship("AssessmentAttempt", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(String(50), primary_key=True, index=True)
    assessment_id = Column(String(50), ForeignKey("assessments.id"), nullable=False, index=True)
    student_id = Column(String(50), default="default_student", index=True)
    score = Column(Float, nullable=False)
    total_points = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=False)
    time_spent_secs = Column(Integer, default=0)
    answers_json = Column(JSON, default=list)  # user answers and question results
    misconceptions_json = Column(JSON, default=list)  # detected misconceptions
    mastery_delta_json = Column(JSON, default=dict)  # changes in BKT mastery per topic
    completed_at = Column(DateTime, default=datetime.datetime.utcnow)

    assessment = relationship("Assessment", back_populates="attempts")
