import os
from typing import List, Dict, Any
from pathlib import Path
import pypdf

class PDFParser:
    """
    Extracts text from PDF documents while preserving exact page provenance.
    Supports scanned page detection and heading heuristics.
    """
    
    @staticmethod
    def extract_pages(file_path: str) -> List[Dict[str, Any]]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        extracted_pages = []
        try:
            reader = pypdf.PdfReader(str(path))
            total_pages = len(reader.pages)
            
            for page_idx, page in enumerate(reader.pages):
                page_num = page_idx + 1  # 1-indexed for academic citations
                text = page.extract_text() or ""
                
                # Clean and detect if text is empty or scanned
                clean_text = text.strip()
                is_scanned = len(clean_text) < 20  # heuristic for image-only/scanned page
                
                # Detect rudimentary headings: first capitalized line or short title line
                lines = [line.strip() for line in clean_text.split("\n") if line.strip()]
                headings = []
                if lines:
                    first_line = lines[0]
                    if len(first_line) < 80 and not first_line.endswith("."):
                        headings.append(first_line)
                
                extracted_pages.append({
                    "page_number": page_num,
                    "text": clean_text,
                    "headings": headings,
                    "is_scanned": is_scanned,
                    "extraction_method": "ocr_simulated" if is_scanned and len(clean_text) > 0 else "text",
                    "confidence": 0.85 if is_scanned else 0.99
                })
                
            return extracted_pages
            
        except Exception as e:
            raise RuntimeError(f"Error parsing PDF file {file_path}: {str(e)}")
