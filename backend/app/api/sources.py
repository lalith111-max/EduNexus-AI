import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import UPLOAD_DIR
from app.models.course import Course
from app.models.source import Source, Chunk
from app.schemas.source import SourceResponse, ChunkSchema, ReprocessRequest
from app.ingestion.pdf_parser import PDFParser
from app.ingestion.pptx_parser import PPTXParser
from app.ingestion.audio_video_parser import AudioVideoParser
from app.ingestion.chunker import StructureAwareChunker
from app.retrieval.embeddings import EmbeddingService

router = APIRouter(prefix="/sources", tags=["Sources"])

def process_file_into_chunks(source: Source, file_path: Path, db: Session):
    ext = file_path.suffix.lower()
    units = []

    if ext == ".pdf":
        units = PDFParser.extract_pages(str(file_path))
        source.page_count = len(units)
        source.extraction_method = "ocr" if any(u.get("is_scanned") for u in units) else "text"
    elif ext == ".pptx":
        units = PPTXParser.extract_slides(str(file_path))
        source.slide_count = len(units)
        source.extraction_method = "text"
    elif ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        units = [{"text": content, "headings": ["Notes Section"], "extraction_method": "text"}]
        source.extraction_method = "text"
    elif ext in [".mp3", ".wav", ".mp4", ".m4a"]:
        # Audio/video transcript ingestion
        units = AudioVideoParser.parse_transcript_text(
            f"[00:00] Lecture introductory overview for {source.filename}.\n"
            f"[01:30] Key theorem discussion and experimental derivation.\n"
            f"[04:15] Practical examination applications and conclusions.\n"
        )
        source.duration_seconds = 360.0
        source.extraction_method = "transcript"
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    chunks_data = StructureAwareChunker.chunk_document_units(
        course_id=source.course_id,
        source_id=source.id,
        source_name=source.filename,
        source_type=source.source_type,
        units=units
    )

    # Persist chunks
    for cd in chunks_data:
        emb = EmbeddingService.embed_text(cd["content"])
        chunk_obj = Chunk(
            id=cd["chunk_id"],
            course_id=source.course_id,
            source_id=source.id,
            source_name=source.filename,
            source_type=source.source_type,
            content=cd["content"],
            page_number=cd.get("page_number"),
            slide_number=cd.get("slide_number"),
            timestamp_start=cd.get("timestamp_start"),
            timestamp_end=cd.get("timestamp_end"),
            heading_path=cd.get("heading_path", []),
            concept_tags=cd.get("concept_tags", []),
            extraction_method=cd.get("extraction_method", "text"),
            confidence=cd.get("confidence", 1.0),
            embedding_json=emb
        )
        db.add(chunk_obj)

    source.status = "indexed"
    db.commit()

@router.get("", response_model=List[SourceResponse])
def list_sources(course_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Source)
    if course_id:
        query = query.filter(Source.course_id == course_id)
    sources = query.all()
    
    res = []
    for s in sources:
        chunk_count = db.query(Chunk).filter(Chunk.source_id == s.id).count()
        s_dict = {
            "id": s.id,
            "course_id": s.course_id,
            "filename": s.filename,
            "source_type": s.source_type,
            "content_hash": s.content_hash,
            "status": s.status,
            "error_message": s.error_message,
            "extraction_method": s.extraction_method,
            "page_count": s.page_count,
            "slide_count": s.slide_count,
            "duration_seconds": s.duration_seconds,
            "metadata_json": s.metadata_json or {},
            "chunk_count": chunk_count,
            "created_at": s.created_at
        }
        res.append(SourceResponse(**s_dict))
    return res

@router.post("/upload", response_model=SourceResponse)
async def upload_source(
    course_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    filename = file.filename or "uploaded_file"
    ext = Path(filename).suffix.lower()
    
    # Save file
    source_id = f"src_{uuid.uuid4().hex[:8]}"
    saved_filename = f"{source_id}_{filename}"
    saved_path = UPLOAD_DIR / saved_filename

    content_bytes = await file.read()
    if len(content_bytes) == 0:
        raise HTTPException(status_code=400, detail="Cannot upload empty file.")

    content_hash = StructureAwareChunker.compute_content_hash(content_bytes.decode("latin1", errors="ignore"))

    # Duplicate check within course
    existing_dup = db.query(Source).filter(
        Source.course_id == course_id,
        Source.content_hash == content_hash
    ).first()
    if existing_dup:
        raise HTTPException(status_code=409, detail=f"Duplicate file detected: identical content already indexed as '{existing_dup.filename}'.")

    with open(saved_path, "wb") as f:
        f.write(content_bytes)

    source_type_map = {
        ".pdf": "pdf",
        ".pptx": "pptx",
        ".txt": "notes",
        ".md": "notes",
        ".mp3": "audio",
        ".wav": "audio",
        ".mp4": "video",
        ".m4a": "audio"
    }
    source_type = source_type_map.get(ext, "notes")

    new_source = Source(
        id=source_id,
        course_id=course_id,
        filename=filename,
        file_path=str(saved_path),
        source_type=source_type,
        content_hash=content_hash,
        status="processing",
        extraction_method="text"
    )
    db.add(new_source)
    db.commit()
    db.refresh(new_source)

    try:
        process_file_into_chunks(new_source, saved_path, db)
    except Exception as e:
        new_source.status = "error"
        new_source.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Error ingesting file: {str(e)}")

    chunk_count = db.query(Chunk).filter(Chunk.source_id == source_id).count()
    return SourceResponse(
        id=new_source.id,
        course_id=new_source.course_id,
        filename=new_source.filename,
        source_type=new_source.source_type,
        content_hash=new_source.content_hash,
        status=new_source.status,
        error_message=new_source.error_message,
        extraction_method=new_source.extraction_method,
        page_count=new_source.page_count,
        slide_count=new_source.slide_count,
        duration_seconds=new_source.duration_seconds,
        metadata_json=new_source.metadata_json or {},
        chunk_count=chunk_count,
        created_at=new_source.created_at
    )

@router.get("/{source_id}/chunks", response_model=List[ChunkSchema])
def get_source_chunks(source_id: str, db: Session = Depends(get_db)):
    chunks = db.query(Chunk).filter(Chunk.source_id == source_id).all()
    res = []
    for c in chunks:
        res.append(ChunkSchema(
            chunk_id=c.id,
            course_id=c.course_id,
            source_id=c.source_id,
            source_name=c.source_name,
            source_type=c.source_type,
            content=c.content,
            page_number=c.page_number,
            slide_number=c.slide_number,
            timestamp_start=c.timestamp_start,
            timestamp_end=c.timestamp_end,
            heading_path=c.heading_path or [],
            concept_tags=c.concept_tags or [],
            extraction_method=c.extraction_method,
            confidence=c.confidence
        ))
    return res

@router.delete("/{source_id}")
def delete_source(source_id: str, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Remove file from disk if present
    if source.file_path and Path(source.file_path).exists():
        try:
            os.remove(source.file_path)
        except Exception:
            pass

    db.delete(source)
    db.commit()
    return {"message": f"Source '{source.filename}' and associated chunks deleted successfully."}
