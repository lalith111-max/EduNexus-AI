from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class BenchmarkTestCase(BaseModel):
    id: str
    question: str
    expected_answer_summary: str
    expected_sources: List[str]
    expected_supported: bool
    topic: str
    difficulty: str
    requires_multi_chunk: bool = False
    is_numerical: bool = False
    is_adversarial_or_negative: bool = False

class EvalMetricSummary(BaseModel):
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float
    citation_validity_rate: float
    refusal_accuracy: float
    latency_ms_avg: float
    total_test_cases: int

class EvalRunResponse(BaseModel):
    run_id: str
    run_name: str
    timestamp: datetime
    metrics: EvalMetricSummary
    test_case_results: List[Dict[str, Any]]
    simulated_cohort_results: Optional[Dict[str, Any]] = None

class SimulationCohortComparison(BaseModel):
    cohort_name: str  # Beginner, Intermediate, Advanced
    initial_mastery: float
    final_mastery_adaptive: float
    final_mastery_random: float
    adaptive_gain_percent: float
    question_repetition_rate: float
    session_count: int
