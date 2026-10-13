import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.course import Course
from app.models.source import Chunk
from app.models.chat import Conversation, Message
from app.schemas.chat import ChatRequest, ChatResponse, ConversationResponse, MessageResponse
from app.retrieval.hybrid_retriever import HybridRetriever
from app.tutor.grounded_tutor import GroundedTutor

router = APIRouter(prefix="/tutor", tags=["Tutor"])

@router.post("/chat", response_model=ChatResponse)
def tutor_chat(req: ChatRequest, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == req.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Ensure conversation
    conv_id = req.conversation_id
    if not conv_id:
        conv_id = f"conv_{uuid.uuid4().hex[:8]}"
        new_conv = Conversation(
            id=conv_id,
            course_id=req.course_id,
            title=f"Question: {req.message[:35]}..."
        )
        db.add(new_conv)
        db.commit()

    # Load all chunks for this course
    chunks = db.query(Chunk).filter(Chunk.course_id == req.course_id).all()
    chunk_dicts = [
        {
            "chunk_id": c.id,
            "course_id": c.course_id,
            "source_id": c.source_id,
            "source_name": c.source_name,
            "source_type": c.source_type,
            "content": c.content,
            "page_number": c.page_number,
            "slide_number": c.slide_number,
            "timestamp_start": c.timestamp_start,
            "timestamp_end": c.timestamp_end,
            "heading_path": c.heading_path or [],
            "concept_tags": c.concept_tags or [],
            "embedding": c.embedding_json
        }
        for c in chunks
    ]

    # Index into hybrid retriever
    retriever = HybridRetriever(alpha=0.55)
    retriever.index(chunk_dicts)

    # Retrieve candidate chunks
    retrieved = retriever.retrieve(req.message, top_k=4, topic_filter=req.topic_filter)

    # Generate grounded tutor response
    response_data = GroundedTutor.generate_grounded_response(
        query=req.message,
        retrieved_items=retrieved,
        depth=req.depth,
        allow_outside=req.allow_outside_knowledge
    )

    # Save messages to conversation history
    user_msg = Message(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        conversation_id=conv_id,
        role="user",
        content=req.message,
        citations_json=[],
        is_grounded=True,
        refused=False,
        confidence_score=1.0
    )
    db.add(user_msg)

    asst_msg = Message(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        conversation_id=conv_id,
        role="assistant",
        content=response_data["content"],
        citations_json=response_data["citations"],
        is_grounded=response_data["is_grounded"],
        refused=response_data["refused"],
        confidence_score=response_data.get("confidence_score", 1.0)
    )
    db.add(asst_msg)
    db.commit()

    return ChatResponse(
        conversation_id=conv_id,
        message_id=asst_msg.id,
        content=response_data["content"],
        citations=response_data["citations"],
        is_grounded=response_data["is_grounded"],
        refused=response_data["refused"],
        refusal_reason=response_data.get("refusal_reason"),
        outside_knowledge_used=response_data.get("outside_knowledge_used", False),
        confidence_score=response_data.get("confidence_score", 1.0),
        retrieved_chunks_count=len(retrieved)
    )

@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(course_id: str, db: Session = Depends(get_db)):
    convs = db.query(Conversation).filter(Conversation.course_id == course_id).order_by(Conversation.created_at.desc()).all()
    res = []
    for c in convs:
        cnt = db.query(Message).filter(Message.conversation_id == c.id).count()
        res.append(ConversationResponse(
            id=c.id,
            course_id=c.course_id,
            title=c.title,
            created_at=c.created_at,
            message_count=cnt
        ))
    return res

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(conversation_id: str, db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()
    return msgs
