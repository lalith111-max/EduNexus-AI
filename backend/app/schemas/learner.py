from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class TopicMasterySchema(BaseModel):
    id: str
    student_id: str
    course_id: str
    topic: str
    p_l: float
    p_t: float
    p_g: float
    p_s: float
    uncertainty: float
    total_attempts: int
    correct_attempts: int
    streak: int
    mastery_status: str  # "needs_attention" | "improving" | "mastered"
    last_practiced: datetime
    next_review_at: datetime
    history: List[Any] = Field(default_factory=list)

    class Config:
        from_attributes = True

class LearnerOverviewResponse(BaseModel):
    student_id: str
    course_id: str
    overall_mastery: float
    total_attempts: int
    average_accuracy: float
    topics: List[TopicMasterySchema]
    strongest_topics: List[str]
    weakest_topics: List[str]
    recent_streak_days: int
    due_reviews_count: int

class RecommendationItem(BaseModel):
    id: str
    type: str  # "revision", "practice_quiz", "concept_review"
    topic: str
    title: str
    reason: str
    mastery_score: float
    priority: str  # "high", "medium", "low"
    prerequisite_blocker: Optional[str] = None
    source_reference: Optional[str] = None

class RevisionPlanResponse(BaseModel):
    student_id: str
    course_id: str
    target_exam_date: Optional[str] = None
    daily_study_mins: int = 30
    schedule_recommendations: List[Dict[str, Any]]
    weak_topic_flashcards: List[Dict[str, Any]]
    formula_cheat_sheets: List[Dict[str, Any]]
    quick_revision_notes: List[Dict[str, Any]]
