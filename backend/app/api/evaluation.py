import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.source import Chunk
from app.models.assessment import Question
from app.models.evaluation import EvalRun
from app.retrieval.hybrid_retriever import HybridRetriever
from app.evaluation.rag_evaluator import RAGEvaluator
from app.evaluation.personalization_sim import PersonalizationSimulator
from app.evaluation.benchmarks import BENCHMARK_TEST_CASES

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Benchmarks"])

@router.post("/run")
def run_evaluation_benchmark(course_id: str = "course_cs101", db: Session = Depends(get_db)):
    """
    Executes live benchmark suite on indexed course materials:
    - Measures RAG Faithfulness, Relevancy, Precision, Recall, Citation Validity Rate, Refusal Accuracy
    - Runs multi-session student cohort simulation (Adaptive vs Non-Adaptive Baseline)
    - Saves run record and returns computed metrics
    """
    # Load chunks for retrieval
    chunks = db.query(Chunk).all()
    if not chunks:
        raise HTTPException(status_code=400, detail="Cannot run evaluation without indexed course chunks.")

    chunk_dicts = [
        {
            "chunk_id": c.id,
            "course_id": c.course_id,
            "source_id": c.source_id,
            "source_name": c.source_name,
            "source_type": c.source_type,
            "content": c.content,
            "page_number": c.page_number,
            "slide_number": c.slide_number,
            "timestamp_start": c.timestamp_start,
            "timestamp_end": c.timestamp_end,
            "heading_path": c.heading_path or [],
            "concept_tags": c.concept_tags or [],
            "embedding": c.embedding_json
        }
        for c in chunks
    ]

    retriever = HybridRetriever(alpha=0.50)
    retriever.index(chunk_dicts)

    # 1. RAG Evaluation
    eval_res = RAGEvaluator.evaluate_retriever_and_tutor(retriever, BENCHMARK_TEST_CASES)
    summary = eval_res["summary"]

    # 2. Personalization Cohort Simulation
    questions = db.query(Question).filter(Question.is_verified == True).all()
    q_dicts = [
        {
            "id": q.id,
            "topic": q.topic,
            "difficulty": q.difficulty,
            "question_text": q.question_text
        }
        for q in questions
    ]
    if not q_dicts:
        # Create minimal simulated pool if DB questions not yet seeded
        q_dicts = [
            {"id": f"q_{i}", "topic": "Algorithms", "difficulty": "medium", "question_text": f"Q{i}"}
            for i in range(10)
        ]

    sim_res = PersonalizationSimulator.run_cohort_simulation(q_dicts, num_sessions=5)

    run_id = f"eval_{uuid.uuid4().hex[:8]}"
    run_record = EvalRun(
        id=run_id,
        run_name=f"Automated Benchmark Run ({datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')})",
        timestamp=datetime.datetime.utcnow(),
        total_samples=summary["total_test_cases"],
        faithfulness=summary["faithfulness"],
        answer_relevancy=summary["answer_relevancy"],
        context_precision=summary["context_precision"],
        context_recall=summary["context_recall"],
        citation_validity_rate=summary["citation_validity_rate"],
        refusal_accuracy=summary["refusal_accuracy"],
        latency_ms_avg=summary["latency_ms_avg"],
        details_json={
            "rag_results": eval_res["results"],
            "simulation": sim_res
        }
    )
    db.add(run_record)
    db.commit()

    return {
        "run_id": run_id,
        "run_name": run_record.run_name,
        "timestamp": run_record.timestamp,
        "metrics": summary,
        "test_case_results": eval_res["results"],
        "simulated_cohort_results": sim_res
    }

@router.get("/results")
def get_evaluation_results(db: Session = Depends(get_db)):
    runs = db.query(EvalRun).order_by(EvalRun.timestamp.desc()).all()
    res = []
    for r in runs:
        res.append({
            "run_id": r.id,
            "run_name": r.run_name,
            "timestamp": r.timestamp,
            "metrics": {
                "faithfulness": r.faithfulness,
                "answer_relevancy": r.answer_relevancy,
                "context_precision": r.context_precision,
                "context_recall": r.context_recall,
                "citation_validity_rate": r.citation_validity_rate,
                "refusal_accuracy": r.refusal_accuracy,
                "latency_ms_avg": r.latency_ms_avg,
                "total_test_cases": r.total_samples
            },
            "test_case_results": (r.details_json or {}).get("rag_results", []),
            "simulated_cohort_results": (r.details_json or {}).get("simulation")
        })
    return res
