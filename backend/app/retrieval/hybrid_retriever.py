import re
from typing import List, Dict, Any, Tuple, Optional
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.vector_store import VectorStore
from app.retrieval.embeddings import EmbeddingService

class HybridRetriever:
    """
    Hybrid retriever fusing lexical BM25 and dense vector cosine similarity.
    Maintains course-level indices and provides relevance confidence scoring.
    """

    def __init__(self, alpha: float = 0.5):
        """
        alpha: weight for lexical BM25 (1-alpha is weight for dense vector)
        """
        self.alpha = alpha
        self.bm25 = BM25Retriever()
        self.vector_store = VectorStore()
        self.chunks: List[Dict[str, Any]] = []

    def index(self, chunks: List[Dict[str, Any]]):
        self.chunks = chunks
        self.bm25.index_chunks(chunks)

        # Prepare dense vectors
        chunks_with_vec = []
        for c in chunks:
            if "embedding" not in c or not c["embedding"]:
                c_copy = dict(c)
                c_copy["embedding"] = EmbeddingService.embed_text(c["content"])
                chunks_with_vec.append(c_copy)
            else:
                chunks_with_vec.append(c)

        self.vector_store.index_chunks(chunks_with_vec)

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        topic_filter: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        if not self.chunks:
            return []

        # 1. Lexical retrieval
        bm25_results = self.bm25.search(query, top_k=top_k * 2)
        bm25_dict = {item[0]["chunk_id"]: item[1] for item in bm25_results}
        max_bm25 = max(bm25_dict.values()) if bm25_dict else 1.0

        # 2. Vector retrieval
        q_vec = EmbeddingService.embed_query(query)
        vec_results = self.vector_store.search(q_vec, top_k=top_k * 2)
        vec_dict = {item[0]["chunk_id"]: item[1] for item in vec_results}
        max_vec = max(vec_dict.values()) if vec_dict else 1.0

        # 3. Fuse scores
        all_candidate_ids = set(bm25_dict.keys()).union(set(vec_dict.keys()))
        chunk_map = {c["chunk_id"]: c for c in self.chunks}

        fused_scores: List[Tuple[Dict[str, Any], float]] = []

        for cid in all_candidate_ids:
            chunk = chunk_map.get(cid)
            if not chunk:
                continue

            # Topic filter if specified
            if topic_filter:
                c_tags = [t.lower() for t in chunk.get("concept_tags", [])]
                h_path = [h.lower() for h in chunk.get("heading_path", [])]
                if topic_filter.lower() not in c_tags and not any(topic_filter.lower() in h for h in h_path):
                    continue

            # Normalized BM25 score in [0, 1]
            has_bm25 = cid in bm25_dict
            norm_bm25 = (bm25_dict[cid] / max_bm25) if has_bm25 and max_bm25 > 0 else 0.0
            # Dense vector cosine similarity
            norm_vec = max(0.0, min(1.0, vec_dict.get(cid, 0.0)))

            if not has_bm25:
                # Lack of lexical keyword anchor indicates off-topic or out-of-corpus query
                combined_score = norm_vec * 0.15
            else:
                combined_score = (self.alpha * norm_bm25) + ((1.0 - self.alpha) * norm_vec)

            fused_scores.append((chunk, combined_score))

        fused_scores.sort(key=lambda x: x[1], reverse=True)
        return fused_scores[:top_k]

    @classmethod
    def compute_query_coverage(cls, query: str, chunk_text: str) -> float:
        tokens = BM25Retriever.tokenize(query)
        if not tokens:
            return 0.0
        clean_text = chunk_text.lower()
        matched = sum(1 for t in tokens if re.search(r"\b" + re.escape(t) + r"\b", clean_text))
        return matched / len(tokens)

    @classmethod
    def assess_evidence_coverage(cls, query: str, retrieved: List[Tuple[Dict[str, Any], float]], threshold: float = 0.28) -> Dict[str, Any]:
        """
        Evaluates whether retrieved evidence contains genuine coverage of the query's core concepts.
        Abstains if score is low, token coverage is insufficient (<30%), or adversarial attempts are detected.
        """
        # Adversarial / prompt injection defense
        if re.search(r"(ignore\s+(all\s+)?previous|reveal\s+.*password|system\s+administrative)", query.lower()):
            return {
                "has_sufficient_evidence": False,
                "confidence": 0.0,
                "reason": "Security safeguard: Disallowed query pattern detected."
            }

        if not retrieved:
            return {
                "has_sufficient_evidence": False,
                "confidence": 0.0,
                "reason": "No matching course material found for this query."
            }

        top_score = retrieved[0][1]
        top_chunk_text = retrieved[0][0].get("content", "")
        coverage = cls.compute_query_coverage(query, top_chunk_text)

        # Requires both score >= threshold and coverage >= 30%
        if top_score < threshold or coverage < 0.30:
            return {
                "has_sufficient_evidence": False,
                "confidence": top_score * coverage,
                "reason": f"Insufficient course evidence (score {top_score:.2f}, content coverage {coverage:.0%})."
            }

        return {
            "has_sufficient_evidence": True,
            "confidence": top_score,
            "reason": "Sufficient source-grounded evidence retrieved."
        }
