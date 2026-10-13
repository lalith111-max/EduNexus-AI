import math
import re
from typing import List, Dict, Any, Tuple

class BM25Retriever:
    """
    Okapi BM25 lexical search implementation.
    Operates in-memory over indexed chunks with k1 and b parameter tuning.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avg_doc_len = 0.0
        self.doc_lens: List[int] = []
        self.doc_term_freqs: List[Dict[str, int]] = []
        self.idf: Dict[str, float] = {}
        self.chunk_ids: List[str] = []
        self.chunks_data: List[Dict[str, Any]] = []

    STOP_WORDS = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
        "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
        "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further", "had",
        "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how",
        "i", "if", "in", "into", "is", "it", "its", "itself", "me", "more", "most", "my", "myself", "no",
        "nor", "not", "of", "off", "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out",
        "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the", "their", "theirs",
        "them", "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too",
        "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which", "while",
        "who", "whom", "why", "with", "you", "your", "yours", "yourself", "yourselves"
    }

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        # Lowercase, find alphanumeric tokens, filter out standard stop words
        tokens = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())
        return [t for t in tokens if t not in cls.STOP_WORDS]

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        self.chunks_data = chunks
        self.chunk_ids = [c["chunk_id"] for c in chunks]
        self.corpus_size = len(chunks)
        self.doc_lens = []
        self.doc_term_freqs = []
        self.idf = {}

        if self.corpus_size == 0:
            self.avg_doc_len = 0.0
            return

        df: Dict[str, int] = {}
        total_len = 0

        for chunk in chunks:
            text = chunk.get("content", "") + " " + " ".join(chunk.get("heading_path", [])) + " " + " ".join(chunk.get("concept_tags", []))
            tokens = self.tokenize(text)
            doc_len = len(tokens)
            self.doc_lens.append(doc_len)
            total_len += doc_len

            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.doc_term_freqs.append(tf)

            for t in tf.keys():
                df[t] = df.get(t, 0) + 1

        self.avg_doc_len = total_len / self.corpus_size if self.corpus_size > 0 else 1.0

        for term, freq in df.items():
            # Standard Lucene/BM25 IDF formula with smoothing
            self.idf[term] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if self.corpus_size == 0:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores: List[float] = [0.0] * self.corpus_size

        for term in query_tokens:
            if term not in self.idf:
                continue
            idf_val = self.idf[term]

            for i in range(self.corpus_size):
                tf = self.doc_term_freqs[i].get(term, 0)
                if tf == 0:
                    continue
                doc_len = self.doc_lens[i]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[i] += idf_val * (numerator / denominator)

        # Pair scores with chunks
        ranked = []
        for i, score in enumerate(scores):
            if score > 0.0:
                ranked.append((self.chunks_data[i], score))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[:top_k]
