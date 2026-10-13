import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from app.core.database import Base

class EvalRun(Base):
    """
    RAG & Personalization Benchmark Evaluation Run Record:
    Stores actual computed metrics:
    - faithfulness: [0.0, 1.0]
    - answer_relevancy: [0.0, 1.0]
    - context_precision: [0.0, 1.0]
    - context_recall: [0.0, 1.0]
    - citation_validity_rate: [0.0, 1.0]
    - refusal_accuracy: [0.0, 1.0]
    """
    __tablename__ = "eval_runs"

    id = Column(String(50), primary_key=True, index=True)
    run_name = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    total_samples = Column(Integer, default=0)
    
    # RAG Metrics
    faithfulness = Column(Float, nullable=False)
    answer_relevancy = Column(Float, nullable=False)
    context_precision = Column(Float, nullable=False)
    context_recall = Column(Float, nullable=False)
    citation_validity_rate = Column(Float, nullable=False)
    refusal_accuracy = Column(Float, nullable=False)
    
    # Latency & details
    latency_ms_avg = Column(Float, default=0.0)
    details_json = Column(JSON, default=dict)
