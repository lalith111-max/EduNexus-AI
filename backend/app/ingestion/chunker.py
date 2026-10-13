import hashlib
import re
from typing import List, Dict, Any, Optional

class StructureAwareChunker:
    """
    Structure and heading-aware chunker that preserves strict source provenance:
    page numbers, slide numbers, video timestamps, headings, and extraction methods.
    """

    MAX_CHUNK_CHARS = 900
    MIN_CHUNK_CHARS = 100
    OVERLAP_CHARS = 120

    COMMON_CONCEPT_KEYWORDS = {
        "algorithm", "complexity", "big-o", "recursion", "dynamic programming",
        "divide and conquer", "binary search", "graph", "tree", "bfs", "dfs",
        "sorting", "sort", "quicksort", "mergesort", "hash table", "dna", "rna", "transcription", "translation",
        "mitosis", "meiosis", "enzyme", "atp", "cellular respiration", "photosynthesis",
        "formula", "equation", "proof", "theorem", "definition", "lemma"
    }

    @staticmethod
    def compute_content_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    def extract_concept_tags(cls, text: str, headings: Optional[List[str]] = None) -> List[str]:
        full_text = text.lower()
        if headings:
            full_text += " " + " ".join([h.lower() for h in headings])
        tags = set()
        for kw in cls.COMMON_CONCEPT_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", full_text):
                if kw in ["quicksort", "mergesort", "sort"]:
                    tags.add("sorting")
                else:
                    tags.add(kw)
        return sorted(list(tags))

    @classmethod
    def split_into_paragraphs(cls, text: str) -> List[str]:
        # Split on double newlines or large spacing
        paragraphs = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paragraphs if p.strip()]

    @classmethod
    def chunk_document_units(
        cls,
        course_id: str,
        source_id: str,
        source_name: str,
        source_type: str,
        units: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Takes raw extracted units (from PDF pages, PPTX slides, audio segments, or notes)
        and converts them into stable, provenance-grounded chunk records.
        """
        chunks = []
        global_chunk_idx = 0

        for unit in units:
            page_num = unit.get("page_number")
            slide_num = unit.get("slide_number")
            t_start = unit.get("timestamp_start")
            t_end = unit.get("timestamp_end")
            headings = unit.get("headings", [])
            ext_method = unit.get("extraction_method", "text")
            confidence = unit.get("confidence", 1.0)
            unit_text = unit.get("text", "").strip()

            if not unit_text:
                continue

            # If unit text is relatively short, keep it as a single chunk to preserve full context
            if len(unit_text) <= cls.MAX_CHUNK_CHARS:
                sub_chunks = [unit_text]
            else:
                # Structure-aware paragraph split
                paragraphs = cls.split_into_paragraphs(unit_text)
                sub_chunks = []
                current_acc = []
                current_len = 0

                for para in paragraphs:
                    if current_len + len(para) > cls.MAX_CHUNK_CHARS and current_acc:
                        sub_chunks.append("\n\n".join(current_acc))
                        current_acc = [para]
                        current_len = len(para)
                    else:
                        current_acc.append(para)
                        current_len += len(para)

                if current_acc:
                    sub_chunks.append("\n\n".join(current_acc))

            for sub_idx, chunk_text in enumerate(sub_chunks):
                global_chunk_idx += 1
                
                # Construct human-readable and deterministic stable chunk ID
                prefix = f"{source_id}"
                if page_num is not None:
                    chunk_id = f"{prefix}_p{page_num}_c{sub_idx + 1}"
                elif slide_num is not None:
                    chunk_id = f"{prefix}_s{slide_num}_c{sub_idx + 1}"
                elif t_start is not None:
                    chunk_id = f"{prefix}_t{int(t_start)}_c{sub_idx + 1}"
                else:
                    chunk_id = f"{prefix}_c{global_chunk_idx}"

                concept_tags = cls.extract_concept_tags(chunk_text, headings=headings)

                chunks.append({
                    "chunk_id": chunk_id,
                    "course_id": course_id,
                    "source_id": source_id,
                    "source_name": source_name,
                    "source_type": source_type,
                    "content": chunk_text,
                    "page_number": page_num,
                    "slide_number": slide_num,
                    "timestamp_start": t_start,
                    "timestamp_end": t_end,
                    "heading_path": headings,
                    "concept_tags": concept_tags,
                    "extraction_method": ext_method,
                    "confidence": confidence
                })

        return chunks
