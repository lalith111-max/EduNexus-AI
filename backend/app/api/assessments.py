import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.course import Course
from app.models.assessment import Question, Assessment, AssessmentAttempt
from app.models.learner import TopicMastery, LearnerEvidence
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentResponse,
    QuestionPublic,
    AssessmentSubmitRequest,
    AssessmentResultResponse
)
from app.assessment.engine import AssessmentEngine
from app.assessment.scorer import AssessmentScorer
from app.learner.bkt import BayesianKnowledgeTracing

router = APIRouter(prefix="/assessments", tags=["Assessments"])

@router.post("/generate", response_model=AssessmentResponse)
def generate_assessment(req: AssessmentCreate, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == req.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Fetch candidate verified questions for this course
    q_query = db.query(Question).filter(
        Question.course_id == req.course_id,
        Question.is_verified == True
    )
    if req.topic:
        q_query = q_query.filter(Question.topic == req.topic)
    
    candidate_records = q_query.all()
    if not candidate_records:
        # Fall back to any verified questions in course
        candidate_records = db.query(Question).filter(Question.course_id == req.course_id).all()

    if not candidate_records:
        raise HTTPException(status_code=400, detail="No verified questions found for this course. Please index course materials first.")

    # Get student mastery to guide adaptive selection
    target_topic = req.topic or (candidate_records[0].topic if candidate_records else "General")
    mastery_record = db.query(TopicMastery).filter(
        TopicMastery.course_id == req.course_id,
        TopicMastery.topic == target_topic
    ).first()
    current_p_l = mastery_record.p_l if mastery_record else 0.20

    question_dicts = [
        {
            "id": q.id,
            "topic": q.topic,
            "concept_id": q.concept_id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "options": q.options_json,
            "correct_answer": q.correct_answer,
            "explanation": q.explanation,
            "tolerance": q.tolerance,
            "citations": q.citations or []
        }
        for q in candidate_records
    ]

    selected_questions = AssessmentEngine.select_adaptive_questions(
        candidate_questions=question_dicts,
        student_mastery_p_l=current_p_l,
        num_questions=min(req.num_questions, len(question_dicts)),
        target_topic=req.topic
    )

    assessment_id = f"asmt_{uuid.uuid4().hex[:8]}"
    title = f"{req.mode.capitalize()} Quiz: {target_topic}"

    new_asmt = Assessment(
        id=assessment_id,
        course_id=req.course_id,
        title=title,
        mode=req.mode,
        topic=target_topic,
        time_limit_mins=req.time_limit_mins,
        questions_json=selected_questions
    )
    db.add(new_asmt)
    db.commit()

    public_qs = [
        QuestionPublic(
            id=q["id"],
            topic=q["topic"],
            question_text=q["question_text"],
            question_type=q["question_type"],
            difficulty=q["difficulty"],
            options=q.get("options"),
            citations=q.get("citations", [])
        )
        for q in selected_questions
    ]

    return AssessmentResponse(
        id=new_asmt.id,
        course_id=new_asmt.course_id,
        title=new_asmt.title,
        mode=new_asmt.mode,
        topic=new_asmt.topic,
        time_limit_mins=new_asmt.time_limit_mins,
        questions=public_qs,
        total_questions=len(public_qs),
        created_at=new_asmt.created_at
    )

@router.get("/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    asmt = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not asmt:
        raise HTTPException(status_code=404, detail="Assessment not found")

    public_qs = [
        QuestionPublic(
            id=q["id"],
            topic=q["topic"],
            question_text=q["question_text"],
            question_type=q["question_type"],
            difficulty=q["difficulty"],
            options=q.get("options"),
            citations=q.get("citations", [])
        )
        for q in asmt.questions_json
    ]

    return AssessmentResponse(
        id=asmt.id,
        course_id=asmt.course_id,
        title=asmt.title,
        mode=asmt.mode,
        topic=asmt.topic,
        time_limit_mins=asmt.time_limit_mins,
        questions=public_qs,
        total_questions=len(public_qs),
        created_at=asmt.created_at
    )

@router.post("/{assessment_id}/submit", response_model=AssessmentResultResponse)
def submit_assessment(
    assessment_id: str,
    req: AssessmentSubmitRequest,
    db: Session = Depends(get_db)
):
    asmt = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not asmt:
        raise HTTPException(status_code=404, detail="Assessment not found")

    ans_map = {a.question_id: a.answer for a in req.answers}
    q_results, misconceptions, score, max_score = AssessmentScorer.score_attempt(
        questions=asmt.questions_json,
        user_answers=ans_map
    )

    accuracy = (score / max_score) if max_score > 0 else 0.0

    # Update BKT Learner Mastery per topic
    mastery_deltas: Dict[str, Dict[str, float]] = {}
    weak_topics_set = set()

    for qr in q_results:
        topic_name = qr.topic
        mastery = db.query(TopicMastery).filter(
            TopicMastery.student_id == req.student_id,
            TopicMastery.course_id == asmt.course_id,
            TopicMastery.topic == topic_name
        ).first()

        if not mastery:
            mastery = TopicMastery(
                id=f"{req.student_id}_{asmt.course_id}_{topic_name.lower().replace(' ', '_')}",
                student_id=req.student_id,
                course_id=asmt.course_id,
                topic=topic_name,
                p_l=0.20,
                uncertainty=0.40,
                total_attempts=0,
                correct_attempts=0,
                streak=0,
                history_json=[]
            )
            db.add(mastery)
            db.flush()

        prior_p_l = mastery.p_l
        is_corr = qr.is_correct
        next_p_l, posterior, new_unc = BayesianKnowledgeTracing.update_mastery(
            current_p_l=prior_p_l,
            is_correct=is_corr,
            total_attempts=mastery.total_attempts
        )

        mastery.p_l = next_p_l
        mastery.uncertainty = new_unc
        mastery.total_attempts += 1
        if is_corr:
            mastery.correct_attempts += 1
            mastery.streak += 1
        else:
            mastery.streak = 0
            weak_topics_set.add(topic_name)

        # Log evidence
        evidence = LearnerEvidence(
            id=f"ev_{uuid.uuid4().hex[:8]}",
            student_id=req.student_id,
            course_id=asmt.course_id,
            topic=topic_name,
            question_id=qr.question_id,
            is_correct=1 if is_corr else 0,
            prior_p_l=prior_p_l,
            posterior_p_l=next_p_l
        )
        db.add(evidence)

        mastery_deltas[topic_name] = {
            "prior": round(prior_p_l, 2),
            "posterior": round(next_p_l, 2),
            "delta": round(next_p_l - prior_p_l, 2)
        }

    attempt_id = f"atm_{uuid.uuid4().hex[:8]}"
    attempt = AssessmentAttempt(
        id=attempt_id,
        assessment_id=assessment_id,
        student_id=req.student_id,
        score=score,
        total_points=max_score,
        accuracy=round(accuracy, 2),
        time_spent_secs=req.time_spent_secs,
        answers_json=[qr.model_dump() for qr in q_results],
        misconceptions_json=[m.model_dump() for m in misconceptions],
        mastery_delta_json=mastery_deltas
    )
    db.add(attempt)
    db.commit()

    weak_topics = sorted(list(weak_topics_set))
    rec_action = f"Review foundational citations for {weak_topics[0]} in Revision Studio." if weak_topics else "Outstanding performance! Proceed to advanced synthesis quiz."

    return AssessmentResultResponse(
        attempt_id=attempt_id,
        assessment_id=assessment_id,
        student_id=req.student_id,
        score=score,
        total_points=max_score,
        accuracy=round(accuracy, 2),
        time_spent_secs=req.time_spent_secs,
        question_results=q_results,
        misconceptions=misconceptions,
        mastery_deltas=mastery_deltas,
        weak_topics=weak_topics,
        recommended_next_action=rec_action,
        completed_at=attempt.completed_at
    )
