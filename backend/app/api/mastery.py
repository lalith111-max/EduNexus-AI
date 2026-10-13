from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.course import Course
from app.models.source import Chunk
from app.models.concept import PrerequisiteEdge
from app.models.learner import TopicMastery, LearnerEvidence
from app.schemas.learner import (
    TopicMasterySchema,
    LearnerOverviewResponse,
    RecommendationItem,
    RevisionPlanResponse
)
from app.learner.bkt import BayesianKnowledgeTracing
from app.learner.recommender import LearnerRecommender

router = APIRouter(prefix="", tags=["Learner Mastery & Revision"])

@router.get("/mastery", response_model=LearnerOverviewResponse)
def get_learner_mastery(
    course_id: str,
    student_id: str = "default_student",
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    masteries = db.query(TopicMastery).filter(
        TopicMastery.course_id == course_id,
        TopicMastery.student_id == student_id
    ).all()

    topic_schemas = []
    total_att = 0
    total_corr = 0
    p_l_sum = 0.0

    for m in masteries:
        total_att += m.total_attempts
        total_corr += m.correct_attempts
        p_l_sum += m.p_l
        status = BayesianKnowledgeTracing.get_mastery_label(m.p_l)

        topic_schemas.append(TopicMasterySchema(
            id=m.id,
            student_id=m.student_id,
            course_id=m.course_id,
            topic=m.topic,
            p_l=round(m.p_l, 2),
            p_t=m.p_t,
            p_g=m.p_g,
            p_s=m.p_s,
            uncertainty=round(m.uncertainty, 2),
            total_attempts=m.total_attempts,
            correct_attempts=m.correct_attempts,
            streak=m.streak,
            mastery_status=status,
            last_practiced=m.last_practiced,
            next_review_at=m.next_review_at,
            history=m.history_json or []
        ))

    num_topics = len(masteries)
    overall_mastery = round(p_l_sum / num_topics, 2) if num_topics > 0 else 0.20
    avg_accuracy = round(total_corr / total_att, 2) if total_att > 0 else 0.0

    # Sort strongest and weakest
    sorted_by_pl = sorted(topic_schemas, key=lambda x: x.p_l, reverse=True)
    strongest = [t.topic for t in sorted_by_pl[:3] if t.p_l >= 0.50]
    weakest = [t.topic for t in sorted_by_pl[::-1][:3] if t.p_l < 0.60]

    return LearnerOverviewResponse(
        student_id=student_id,
        course_id=course_id,
        overall_mastery=overall_mastery,
        total_attempts=total_att,
        average_accuracy=avg_accuracy,
        topics=topic_schemas,
        strongest_topics=strongest,
        weakest_topics=weakest,
        recent_streak_days=3,
        due_reviews_count=len(weakest)
    )

@router.get("/recommendations", response_model=List[RecommendationItem])
def get_recommendations(
    course_id: str,
    student_id: str = "default_student",
    db: Session = Depends(get_db)
):
    masteries = db.query(TopicMastery).filter(
        TopicMastery.course_id == course_id,
        TopicMastery.student_id == student_id
    ).all()

    edges = db.query(PrerequisiteEdge).filter(PrerequisiteEdge.course_id == course_id).all()
    edge_dicts = [{"prereq_topic": e.prereq_concept_id, "target_topic": e.target_concept_id} for e in edges]

    m_dicts = [
        {"topic": m.topic, "p_l": m.p_l, "total_attempts": m.total_attempts}
        for m in masteries
    ]

    recs = LearnerRecommender.generate_recommendations(m_dicts, edge_dicts)
    return [RecommendationItem(**r) for r in recs]

@router.get("/revision-plan", response_model=RevisionPlanResponse)
def get_revision_plan(
    course_id: str,
    student_id: str = "default_student",
    target_exam_date: Optional[str] = "2026-11-01",
    daily_study_mins: int = 45,
    db: Session = Depends(get_db)
):
    chunks = db.query(Chunk).filter(Chunk.course_id == course_id).all()
    chunk_dicts = [
        {
            "content": c.content,
            "source_name": c.source_name,
            "page_number": c.page_number,
            "slide_number": c.slide_number,
            "concept_tags": c.concept_tags
        }
        for c in chunks
    ]

    masteries = db.query(TopicMastery).filter(
        TopicMastery.course_id == course_id,
        TopicMastery.student_id == student_id
    ).all()
    m_dicts = [{"topic": m.topic, "p_l": m.p_l} for m in masteries]

    materials = LearnerRecommender.generate_revision_materials(chunk_dicts, m_dicts)

    # Schedule recommendations
    schedule = [
        {"day": "Day 1 (Immediate)", "focus": "Weakest Prerequisites", "estimated_mins": daily_study_mins, "status": "pending"},
        {"day": "Day 2", "focus": "Targeted MCQ & Formula Drills", "estimated_mins": daily_study_mins, "status": "pending"},
        {"day": "Day 3", "focus": "Flashcard Active Recall", "estimated_mins": daily_study_mins, "status": "pending"},
        {"day": "Day 4", "focus": "Full Mock Exam Simulation", "estimated_mins": daily_study_mins + 15, "status": "pending"},
    ]

    return RevisionPlanResponse(
        student_id=student_id,
        course_id=course_id,
        target_exam_date=target_exam_date,
        daily_study_mins=daily_study_mins,
        schedule_recommendations=schedule,
        weak_topic_flashcards=materials["flashcards"],
        formula_cheat_sheets=materials["formula_sheets"],
        quick_revision_notes=materials["quick_notes"]
    )
