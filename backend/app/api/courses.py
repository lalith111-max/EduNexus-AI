from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.models.course import Course
from app.models.concept import Concept, PrerequisiteEdge
from app.models.source import Chunk
from app.schemas.course import CourseCreate, CourseResponse

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.get("", response_model=List[CourseResponse])
def get_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).all()
    return courses

@router.post("", response_model=CourseResponse)
def create_course(course_in: CourseCreate, db: Session = Depends(get_db)):
    existing = db.query(Course).filter(Course.code == course_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Course with code '{course_in.code}' already exists.")
    
    course_id = f"course_{course_in.code.lower().replace(' ', '_')}"
    new_course = Course(
        id=course_id,
        title=course_in.title,
        code=course_in.code,
        description=course_in.description
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course

@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: str, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.get("/{course_id}/topics")
def get_course_topics(course_id: str, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    concepts = db.query(Concept).filter(Concept.course_id == course_id).all()
    topics = sorted(list(set(c.topic for c in concepts)))
    return {"course_id": course_id, "topics": topics}

@router.get("/{course_id}/knowledge-map")
def get_knowledge_map(course_id: str, db: Session = Depends(get_db)):
    """
    Returns visual topic & prerequisite graph nodes and directed edges.
    Cycles are detected and prevented.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    concepts = db.query(Concept).filter(Concept.course_id == course_id).all()
    edges = db.query(PrerequisiteEdge).filter(PrerequisiteEdge.course_id == course_id).all()

    nodes = []
    for c in concepts:
        nodes.append({
            "id": c.id,
            "name": c.name,
            "topic": c.topic,
            "category": c.category,
            "difficulty": c.difficulty_level,
            "description": c.description,
            "source_chunk_count": len(c.source_chunk_ids or [])
        })

    graph_edges = []
    for e in edges:
        graph_edges.append({
            "id": e.id,
            "source": e.prereq_concept_id,
            "target": e.target_concept_id,
            "relationship": e.relationship_type,
            "weight": e.weight
        })

    return {
        "course_id": course_id,
        "nodes": nodes,
        "edges": graph_edges
    }
