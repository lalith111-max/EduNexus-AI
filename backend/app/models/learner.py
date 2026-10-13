import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from app.core.database import Base

class TopicMastery(Base):
    """
    Bayesian Knowledge Tracing (BKT) Model State per student per topic:
    - p_l: P(L_t) Probability that the student has mastered the topic
    - p_t: P(T) Probability of learning transition on practice
    - p_g: P(G) Probability of guessing correctly without mastery
    - p_s: P(S) Probability of slipping (incorrect answer despite mastery)
    - uncertainty: Variance/standard error of the estimate
    """
    __tablename__ = "topic_mastery"

    id = Column(String(80), primary_key=True, index=True)  # student_id:course_id:topic
    student_id = Column(String(50), default="default_student", index=True)
    course_id = Column(String(50), ForeignKey("courses.id"), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    
    p_l = Column(Float, default=0.20)  # current mastery probability [0.0, 1.0]
    p_t = Column(Float, default=0.15)  # transition probability
    p_g = Column(Float, default=0.25)  # guess probability
    p_s = Column(Float, default=0.10)  # slip probability
    uncertainty = Column(Float, default=0.40)  # confidence/uncertainty band
    
    total_attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    
    last_practiced = Column(DateTime, default=datetime.datetime.utcnow)
    next_review_at = Column(DateTime, default=datetime.datetime.utcnow)
    history_json = Column(JSON, default=list)  # chronological list of [p_l, timestamp, is_correct]


class LearnerEvidence(Base):
    __tablename__ = "learner_evidence"

    id = Column(String(50), primary_key=True, index=True)
    student_id = Column(String(50), default="default_student", index=True)
    course_id = Column(String(50), ForeignKey("courses.id"), nullable=False, index=True)
    topic = Column(String(100), nullable=False)
    question_id = Column(String(50), nullable=True)
    is_correct = Column(Integer, nullable=False)  # 1 for correct, 0 for incorrect
    prior_p_l = Column(Float, nullable=False)
    posterior_p_l = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
