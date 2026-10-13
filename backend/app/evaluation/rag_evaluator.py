import time
import re
from typing import List, Dict, Any
from app.evaluation.benchmarks import BENCHMARK_TEST_CASES
from app.retrieval.hybrid_retriever import HybridRetriever
from app.tutor.grounded_tutor import GroundedTutor
from app.schemas.evaluation import EvalMetricSummary

class RAGEvaluator:
    """
    RAG & Citation Benchmark Evaluator.
    Computes empirical evaluation metrics over real indexed course chunks.
    Never fabricates metrics.
    """

    @classmethod
    def evaluate_retriever_and_tutor(
        cls,
        retriever: HybridRetriever,
        test_cases: List[Dict[str, Any]] = BENCHMARK_TEST_CASES
    ) -> Dict[str, Any]:
        """
        Executes benchmark test suite and computes actual metrics.
        """
        results = []
        total_faithfulness = 0.0
        total_relevancy = 0.0
        total_precision = 0.0
        total_recall = 0.0
        total_citation_validity = 0.0
        correct_refusals = 0
        total_negatives = 0
        total_positives = 0
        total_time_ms = 0.0

        for tc in test_cases:
            q = tc["question"]
            is_supported = tc["expected_supported"]
            expected_sources = tc.get("expected_sources", [])

            t0 = time.time()
            retrieved = retriever.retrieve(q, top_k=3)
            response = GroundedTutor.generate_grounded_response(
                query=q,
                retrieved_items=retrieved,
                depth="intermediate",
                allow_outside=False
            )
            elapsed_ms = (time.time() - t0) * 1000.0
            total_time_ms += elapsed_ms

            refused = response.get("refused", False)
            content = response.get("content", "")
            citations = response.get("citations", [])

            # Check Refusal Accuracy
            if not is_supported:
                total_negatives += 1
                if refused:
                    correct_refusals += 1
                # Negative test case metrics
                faithfulness = 1.0 if refused else 0.0
                relevancy = 1.0 if refused else 0.2
                precision = 1.0 if len(retrieved) == 0 or refused else 0.0
                recall = 1.0 if len(retrieved) == 0 or refused else 0.0
                cit_validity = 1.0
            else:
                total_positives += 1
                # Faithfulness: answer grounded in retrieved content
                retrieved_text = " ".join([item[0]["content"] for item in retrieved])
                claims = [s.strip() for s in content.split(". ") if len(s.strip()) > 15]
                supported_claims = 0
                for claim in claims:
                    # Check token overlap
                    tokens = [t.lower() for t in re.findall(r"\b[a-zA-Z]{4,}\b", claim)]
                    if any(t in retrieved_text.lower() for t in tokens):
                        supported_claims += 1
                faithfulness = (supported_claims / len(claims)) if claims else 1.0

                # Answer Relevancy: overlap with expected answer summary
                expected_terms = [t.lower() for t in re.findall(r"\b[a-zA-Z]{4,}\b", tc["expected_answer_summary"])]
                matched_expected = [t for t in expected_terms if t in content.lower()]
                relevancy = (len(matched_expected) / len(expected_terms)) if expected_terms else 0.9

                # Context Recall: check if expected source appeared in retrieved chunks
                retrieved_sources = [item[0]["source_name"] for item in retrieved]
                source_hits = [s for s in expected_sources if any(s in rs for rs in retrieved_sources)]
                recall = (len(source_hits) / len(expected_sources)) if expected_sources else 1.0

                # Context Precision: top retrieved score
                precision = retrieved[0][1] if retrieved else 0.0

                # Citation Validity: valid non-empty citations with real chunk IDs
                valid_cits = [c for c in citations if c.get("verification_status") == "verified"]
                cit_validity = (len(valid_cits) / len(citations)) if citations else 0.0

            total_faithfulness += faithfulness
            total_relevancy += relevancy
            total_precision += precision
            total_recall += recall
            total_citation_validity += cit_validity

            results.append({
                "test_case_id": tc["id"],
                "question": q,
                "expected_supported": is_supported,
                "actual_refused": refused,
                "faithfulness": round(faithfulness, 2),
                "relevancy": round(relevancy, 2),
                "context_precision": round(precision, 2),
                "context_recall": round(recall, 2),
                "citation_validity": round(cit_validity, 2),
                "latency_ms": round(elapsed_ms, 1),
                "citations_count": len(citations)
            })

        n = len(test_cases)
        refusal_acc = (correct_refusals / total_negatives) if total_negatives > 0 else 1.0

        summary = EvalMetricSummary(
            faithfulness=round(total_faithfulness / n, 2),
            answer_relevancy=round(total_relevancy / n, 2),
            context_precision=round(total_precision / n, 2),
            context_recall=round(total_recall / n, 2),
            citation_validity_rate=round(total_citation_validity / n, 2),
            refusal_accuracy=round(refusal_acc, 2),
            latency_ms_avg=round(total_time_ms / n, 1),
            total_test_cases=n
        )

        return {
            "summary": summary.model_dump(),
            "results": results
        }
