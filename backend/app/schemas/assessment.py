from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.chat import Citation

class QuestionSchema(BaseModel):
    id: str
    course_id: str
    topic: str
    concept_id: Optional[str] = None
    question_text: str
    question_type: str  # mcq, short_answer, numerical
    difficulty: str     # easy, medium, hard
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: str
    rubric: Optional[str] = None
    formula: Optional[str] = None
    tolerance: Optional[float] = 0.01
    source_ids: List[str] = Field(default_factory=list)
    chunk_ids: List[str] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    is_verified: bool = True
    validation_status: str = "valid"

    class Config:
        from_attributes = True

class QuestionPublic(BaseModel):
    id: str
    topic: str
    question_text: str
    question_type: str
    difficulty: str
    options: Optional[List[str]] = None
    citations: List[Citation] = Field(default_factory=list)

class AssessmentCreate(BaseModel):
    course_id: str
    topic: Optional[str] = None
    mode: str = "practice"  # practice, exam, diagnostic
    difficulty: Optional[str] = None
    num_questions: int = 5
    question_types: List[str] = Field(default_factory=lambda: ["mcq", "short_answer", "numerical"])
    time_limit_mins: int = 15

class AssessmentResponse(BaseModel):
    id: str
    course_id: str
    title: str
    mode: str
    topic: Optional[str] = None
    time_limit_mins: int
    questions: List[QuestionPublic]
    total_questions: int
    created_at: datetime

class AnswerSubmission(BaseModel):
    question_id: str
    answer: str

class AssessmentSubmitRequest(BaseModel):
    student_id: str = "default_student"
    time_spent_secs: int = 0
    answers: List[AnswerSubmission]

class QuestionResult(BaseModel):
    question_id: str
    question_text: str
    question_type: str
    topic: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    points_earned: float
    max_points: float
    explanation: str
    citations: List[Citation]
    misconception: Optional[str] = None
    remedial_excerpt: Optional[str] = None

class MisconceptionReport(BaseModel):
    topic: str
    concept: str
    misconception_text: str
    evidence_reasoning: str
    remedial_source_citation: Optional[Citation] = None

class AssessmentResultResponse(BaseModel):
    attempt_id: str
    assessment_id: str
    student_id: str
    score: float
    total_points: float
    accuracy: float
    time_spent_secs: int
    question_results: List[QuestionResult]
    misconceptions: List[MisconceptionReport]
    mastery_deltas: Dict[str, Dict[str, float]]  # {topic: {prior: x, posterior: y, delta: z}}
    weak_topics: List[str]
    recommended_next_action: str
    completed_at: datetime
