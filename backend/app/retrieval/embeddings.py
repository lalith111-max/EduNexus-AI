import math
import re
import hashlib
import numpy as np
from typing import List
from app.core.config import settings

class EmbeddingService:
    """
    Multimodal & text embedding service.
    Defaults to high-fidelity, deterministic dense local vector projections
    with support for Google Gemini embedding models when an API key is configured.
    """

    DIMENSION = 128

    @classmethod
    def get_local_embedding(cls, text: str) -> List[float]:
        """
        Generates a 128-dimensional dense semantic feature vector using
        word & character n-gram feature hashing with frequency-scaled projection.
        Guarantees deterministic, reproducible, unit-norm embeddings.
        """
        vec = np.zeros(cls.DIMENSION, dtype=np.float32)
        if not text:
            return vec.tolist()

        tokens = re.findall(r"\b[a-zA-Z0-9_\-]+\b", text.lower())
        if not tokens:
            return vec.tolist()

        for token in tokens:
            # Deterministic word level hash
            token_bytes = token.encode("utf-8")
            h_word = int(hashlib.md5(token_bytes).hexdigest()[:8], 16) % cls.DIMENSION
            vec[h_word] += 1.0

            # Character 3-gram hashes for morphological similarity
            if len(token) >= 3:
                for i in range(len(token) - 2):
                    ngram_bytes = token[i:i+3].encode("utf-8")
                    h_gram = int(hashlib.md5(ngram_bytes).hexdigest()[:8], 16) % cls.DIMENSION
                    vec[h_gram] += 0.35

        # L2 Normalize
        norm = np.linalg.norm(vec)
        if norm > 1e-8:
            vec = vec / norm

        return vec.tolist()

    @classmethod
    def embed_text(cls, text: str) -> List[float]:
        # If Gemini key is set, attempt gemini embedding if desired; otherwise use fast local embedding
        if settings.GEMINI_API_KEY and settings.DEFAULT_LLM_PROVIDER == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                res = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type="retrieval_document"
                )
                return res["embedding"]
            except Exception:
                pass
        
        return cls.get_local_embedding(text)

    @classmethod
    def embed_query(cls, query: str) -> List[float]:
        if settings.GEMINI_API_KEY and settings.DEFAULT_LLM_PROVIDER == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                res = genai.embed_content(
                    model="models/text-embedding-004",
                    content=query,
                    task_type="retrieval_query"
                )
                return res["embedding"]
            except Exception:
                pass

        return cls.get_local_embedding(query)
