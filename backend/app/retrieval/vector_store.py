import numpy as np
from typing import List, Dict, Any, Tuple

class VectorStore:
    """
    In-memory vector store computing exact Cosine Similarity
    with normalized dense vectors.
    """

    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.vectors: np.ndarray = np.empty((0, 128), dtype=np.float32)

    def index_chunks(self, chunks_with_embeddings: List[Dict[str, Any]]):
        self.chunks = chunks_with_embeddings
        if not chunks_with_embeddings:
            self.vectors = np.empty((0, 128), dtype=np.float32)
            return

        vec_list = [c["embedding"] for c in chunks_with_embeddings]
        self.vectors = np.array(vec_list, dtype=np.float32)

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if len(self.chunks) == 0 or self.vectors.shape[0] == 0:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        norm_q = np.linalg.norm(q_vec)
        if norm_q > 1e-8:
            q_vec = q_vec / norm_q

        # Cosine similarity is dot product of normalized vectors
        scores = np.dot(self.vectors, q_vec)

        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            results.append((self.chunks[idx], score))

        return results
