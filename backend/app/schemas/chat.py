from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class Citation(BaseModel):
    citation_id: str
    source_id: str
    source_name: str
    source_type: str
    chunk_id: str
    page_number: Optional[int] = None
    slide_number: Optional[int] = None
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None
    excerpt: str
    relevance_score: float = 1.0
    verification_status: str = "verified"  # verified, unverified

class ChatRequest(BaseModel):
    course_id: str
    conversation_id: Optional[str] = None
    message: str
    depth: str = "intermediate"  # beginner, intermediate, advanced, exam
    topic_filter: Optional[str] = None
    allow_outside_knowledge: bool = False

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    content: str
    citations: List[Citation] = Field(default_factory=list)
    is_grounded: bool = True
    refused: bool = False
    refusal_reason: Optional[str] = None
    outside_knowledge_used: bool = False
    confidence_score: float = 1.0
    retrieved_chunks_count: int = 0

class ConversationResponse(BaseModel):
    id: str
    course_id: str
    title: str
    created_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    citations_json: List[Citation] = Field(default_factory=list)
    is_grounded: bool = True
    refused: bool = False
    confidence_score: float = 1.0
    created_at: datetime

    class Config:
        from_attributes = True
