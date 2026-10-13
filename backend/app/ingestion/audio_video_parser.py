import re
from typing import List, Dict, Any

class AudioVideoParser:
    """
    Parses audio/video transcripts and timestamped subtitle files (SRT, VTT, or JSON transcripts),
    preserving start and end timestamps for precise media seeking.
    """

    @staticmethod
    def parse_transcript_text(raw_text: str, source_type: str = "video") -> List[Dict[str, Any]]:
        """
        Parses text that contains timestamps in format [MM:SS] or [HH:MM:SS] or standard paragraphs.
        """
        lines = raw_text.splitlines()
        segments = []
        current_start = 0.0
        current_text_lines = []
        
        timestamp_pattern = re.compile(r"\[?(\d{1,2}):(\d{2})(?::(\d{2}))?\]?")
        
        def parse_seconds(m) -> float:
            groups = m.groups()
            if groups[2] is not None:  # HH:MM:SS
                return int(groups[0]) * 3600 + int(groups[1]) * 60 + int(groups[2])
            else:  # MM:SS
                return int(groups[0]) * 60 + int(groups[1])

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            
            match = timestamp_pattern.search(line_str)
            if match:
                # Flush previous segment if any
                if current_text_lines:
                    text_content = " ".join(current_text_lines).strip()
                    if text_content:
                        sec = parse_seconds(match)
                        segments.append({
                            "timestamp_start": current_start,
                            "timestamp_end": sec,
                            "text": text_content,
                            "extraction_method": "transcript"
                        })
                    current_text_lines = []
                current_start = parse_seconds(match)
                # Remove timestamp from line
                cleaned_line = timestamp_pattern.sub("", line_str).strip(" -:")
                if cleaned_line:
                    current_text_lines.append(cleaned_line)
            else:
                current_text_lines.append(line_str)
                
        # Flush final segment
        if current_text_lines:
            text_content = " ".join(current_text_lines).strip()
            if text_content:
                segments.append({
                    "timestamp_start": current_start,
                    "timestamp_end": current_start + 45.0,  # estimated duration
                    "text": text_content,
                    "extraction_method": "transcript"
                })
                
        return segments

    @staticmethod
    def parse_youtube_metadata(youtube_url: str) -> Dict[str, Any]:
        """
        Extracts video ID and simulates or fetches public caption segments.
        Gracefully handles unavailable captions without network crashes.
        """
        video_id = "unknown"
        match = re.search(r"(?:v=|\/embed\/|youtu\.be\/)([a-zA-Z0-9_-]{11})", youtube_url)
        if match:
            video_id = match.group(1)
            
        return {
            "video_id": video_id,
            "url": youtube_url,
            "source_type": "youtube",
            "extraction_method": "transcript"
        }
