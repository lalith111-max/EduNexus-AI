from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChunkSchema(BaseModel):
    chunk_id: str
    course_id: str
    source_id: str
    source_name: str
    source_type: str  # pdf, pptx, notes, audio, video, youtube
    content: str
    page_number: Optional[int] = None
    slide_number: Optional[int] = None
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None
    heading_path: List[str] = Field(default_factory=list)
    concept_tags: List[str] = Field(default_factory=list)
    extraction_method: str = "text"
    confidence: Optional[float] = 1.0

    class Config:
        from_attributes = True

class SourceResponse(BaseModel):
    id: str
    course_id: str
    filename: str
    source_type: str
    content_hash: str
    status: str
    error_message: Optional[str] = None
    extraction_method: str
    page_count: Optional[int] = None
    slide_count: Optional[int] = None
    duration_seconds: Optional[float] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    chunk_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

class ReprocessRequest(BaseModel):
    force_ocr: bool = False
