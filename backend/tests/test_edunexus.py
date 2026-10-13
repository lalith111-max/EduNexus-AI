import pytest
import math
from pathlib import Path
from app.core.config import SAMPLE_DATA_DIR
from app.core.database import SessionLocal, init_db
from app.models.course import Course
from app.models.source import Source, Chunk
from app.models.assessment import Question
from app.models.learner import TopicMastery
from app.ingestion.pdf_parser import PDFParser
from app.ingestion.pptx_parser import PPTXParser
from app.ingestion.chunker import StructureAwareChunker
from app.retrieval.hybrid_retriever import HybridRetriever
from app.tutor.citation_validator import CitationValidator
from app.tutor.grounded_tutor import GroundedTutor
from app.assessment.validator import AssessmentValidator
from app.assessment.scorer import AssessmentScorer
from app.assessment.engine import AssessmentEngine
from app.learner.bkt import BayesianKnowledgeTracing
from app.evaluation.rag_evaluator import RAGEvaluator
from app.evaluation.benchmarks import BENCHMARK_TEST_CASES

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()

# 1. PDF Page Metadata Preservation Test
def test_pdf_page_metadata_preservation():
    pdf_path = SAMPLE_DATA_DIR / "cs101_algorithms_textbook.pdf"
    assert pdf_path.exists(), "Sample PDF must exist"
    pages = PDFParser.extract_pages(str(pdf_path))
    assert len(pages) == 4, f"Expected 4 pages, got {len(pages)}"
    
    # Verify 1-indexed page numbering
    for idx, p in enumerate(pages):
        assert p["page_number"] == idx + 1
        assert len(p["text"]) > 50
    
    # Page 1 must discuss Asymptotic Analysis
    assert "Asymptotic" in pages[0]["text"]
    # Page 2 must discuss MergeSort / QuickSort
    assert "MergeSort" in pages[1]["text"] or "QuickSort" in pages[1]["text"]
    # Page 3 must discuss Binary Search
    assert "Binary Search" in pages[2]["text"]
    # Page 4 must discuss Dynamic Programming
    assert "Dynamic Programming" in pages[3]["text"]

# 2. PPTX Slide Numbering Test
def test_pptx_slide_numbering_preservation():
    pptx_path = SAMPLE_DATA_DIR / "genetics_lecture_slides.pptx"
    assert pptx_path.exists(), "Sample PPTX must exist"
    slides = PPTXParser.extract_slides(str(pptx_path))
    assert len(slides) == 4, f"Expected 4 slides, got {len(slides)}"
    
    for idx, s in enumerate(slides):
        assert s["slide_number"] == idx + 1
        assert len(s["text"]) > 20

    assert "Dogma" in slides[0]["text"]
    assert "Transcription" in slides[1]["text"]
    assert "Respiration" in slides[2]["text"] or "ATP" in slides[2]["text"]
    assert "Mitosis" in slides[3]["text"] or "Meiosis" in slides[3]["text"]

# 3. Chunk Metadata Propagation Test
def test_chunk_metadata_propagation():
    sample_units = [
        {"page_number": 2, "headings": ["Sorting"], "text": "QuickSort executes in O(n log n) average time.", "extraction_method": "text"}
    ]
    chunks = StructureAwareChunker.chunk_document_units(
        course_id="course_cs101",
        source_id="src_pdf_1",
        source_name="textbook.pdf",
        source_type="pdf",
        units=sample_units
    )
    assert len(chunks) == 1
    c = chunks[0]
    assert c["page_number"] == 2
    assert c["source_name"] == "textbook.pdf"
    assert c["source_type"] == "pdf"
    assert "sorting" in c["concept_tags"] or "algorithm" in c["concept_tags"]
    assert "src_pdf_1_p2" in c["chunk_id"]

# 4. Source Retrieval & Hybrid Ranking Test
def test_hybrid_retrieval():
    test_chunks = [
        {"chunk_id": "c1", "content": "QuickSort worst case is quadratic O(n^2).", "concept_tags": ["sorting"], "heading_path": []},
        {"chunk_id": "c2", "content": "Binary Search has logarithmic O(log n) time.", "concept_tags": ["searching"], "heading_path": []},
        {"chunk_id": "c3", "content": "Photosynthesis converts solar photons into ATP in chloroplasts.", "concept_tags": ["biology"], "heading_path": []}
    ]
    retriever = HybridRetriever(alpha=0.5)
    retriever.index(test_chunks)
    
    results = retriever.retrieve("What is the worst case time complexity of QuickSort?", top_k=1)
    assert len(results) == 1
    assert results[0][0]["chunk_id"] == "c1"
    assert results[0][1] > 0.40

# 5. Citation Validation Test
def test_citation_validation():
    valid_chunks = [
        {"chunk_id": "chunk_101", "source_id": "s1", "source_name": "book.pdf", "source_type": "pdf", "page_number": 5, "content": "Full text of chunk 101."}
    ]
    raw_citations = [
        {"chunk_id": "chunk_101", "excerpt": "Full text"},
        {"chunk_id": "chunk_fake_999", "excerpt": "Hallucinated citation"}
    ]
    validated, validity_rate = CitationValidator.validate_citations(raw_citations, valid_chunks)
    assert len(validated) == 2
    assert validated[0].verification_status == "verified"
    assert validated[0].page_number == 5
    assert validated[1].verification_status == "unverified"
    assert validity_rate == 0.50

# 6. Unsupported Query Abstention Test
def test_unsupported_query_handling():
    test_chunks = [
        {"chunk_id": "c1", "content": "Binary search runs in O(log n).", "concept_tags": ["searching"], "heading_path": []}
    ]
    retriever = HybridRetriever(alpha=0.5)
    retriever.index(test_chunks)

    # Completely unrelated question
    unsupported_query = "What is the capital of Australia and who is the prime minister?"
    retrieved = retriever.retrieve(unsupported_query, top_k=2)
    response = GroundedTutor.generate_grounded_response(
        query=unsupported_query,
        retrieved_items=retrieved,
        allow_outside=False
    )
    assert response["refused"] is True
    assert response["is_grounded"] is False
    assert len(response["citations"]) == 0
    assert "Unsupported" in response["content"]

# 7. Numerical Recalculation & Tolerance Test
def test_numerical_answer_verification():
    # log2(1024) = 10
    is_valid, calc, msg = AssessmentValidator.recalculate_numerical(
        formula="math.log2(1024)",
        variables={},
        expected_answer=10.0,
        tolerance=0.01
    )
    assert is_valid is True
    assert calc == 10.0

    # Test tolerance mismatch
    is_valid_wrong, _, _ = AssessmentValidator.recalculate_numerical(
        formula="math.log2(1024)",
        variables={},
        expected_answer=25.0,
        tolerance=0.01
    )
    assert is_valid_wrong is False

# 8. MCQ Answer-Key Validation Test
def test_mcq_answer_key_validation():
    valid, _ = AssessmentValidator.validate_mcq(
        question_text="What is the worst-case time complexity of QuickSort?",
        options=["O(n)", "O(n log n)", "O(n^2)", "O(1)"],
        correct_answer="O(n^2)"
    )
    assert valid is True

    # Duplicate options failure
    invalid_dup, msg = AssessmentValidator.validate_mcq(
        question_text="Sample question?",
        options=["O(n)", "O(n)", "O(n^2)"],
        correct_answer="O(n)"
    )
    assert invalid_dup is False
    assert "duplicate" in msg.lower()

# 9. Duplicate Question Detection Test
def test_duplicate_question_detection():
    existing = [
        "What is the worst-case time complexity of QuickSort algorithm?",
        "How many ATP molecules are produced during glycolysis?"
    ]
    near_duplicate = "What is the worst-case time complexity of the QuickSort algorithm?"
    distinct_question = "Explain the central dogma of molecular biology."

    is_dup, sim1 = AssessmentValidator.check_duplicate(near_duplicate, existing)
    assert is_dup is True
    assert sim1 > 0.80

    is_dup2, sim2 = AssessmentValidator.check_duplicate(distinct_question, existing)
    assert is_dup2 is False
    assert sim2 < 0.30

# 10. Bayesian Knowledge Tracing Math Test
def test_bkt_posterior_and_transition():
    # Prior: 0.20, P(T)=0.15, P(G)=0.25, P(S)=0.10
    # Correct observation:
    # P(L | C) = 0.20 * 0.90 / (0.20 * 0.90 + 0.80 * 0.25) = 0.18 / (0.18 + 0.20) = 0.18 / 0.38 ≈ 0.47368
    # Transition: P(L_{t+1}) = 0.47368 + (1 - 0.47368) * 0.15 ≈ 0.5526
    next_p_l, posterior, unc = BayesianKnowledgeTracing.update_mastery(
        current_p_l=0.20,
        is_correct=True,
        total_attempts=1,
        p_t=0.15,
        p_g=0.25,
        p_s=0.10
    )
    assert math.isclose(posterior, 0.47368, rel_tol=1e-3)
    assert math.isclose(next_p_l, 0.5526, rel_tol=1e-3)
    assert unc < 0.50

    # Incorrect observation:
    # P(L | I) = 0.20 * 0.10 / (0.20 * 0.10 + 0.80 * 0.75) = 0.02 / (0.02 + 0.60) = 0.02 / 0.62 ≈ 0.03225
    # Transition: 0.03225 + 0.96775 * 0.15 ≈ 0.1774
    next_p_l_inc, posterior_inc, _ = BayesianKnowledgeTracing.update_mastery(
        current_p_l=0.20,
        is_correct=False,
        total_attempts=1,
        p_t=0.15,
        p_g=0.25,
        p_s=0.10
    )
    assert math.isclose(posterior_inc, 0.03225, rel_tol=1e-3)
    assert math.isclose(next_p_l_inc, 0.1774, rel_tol=1e-3)

# 11. End-to-End Ingestion to Retrieval to Citation Integration Test
def test_e2e_ingestion_retrieval_citation():
    db = SessionLocal()
    try:
        # Verify CS101 chunks in DB
        chunks = db.query(Chunk).filter(Chunk.course_id == "course_cs101").all()
        assert len(chunks) >= 4, "CS101 should have indexed chunks"

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

        retriever = HybridRetriever(alpha=0.5)
        retriever.index(chunk_dicts)

        # Query about binary search
        retrieved = retriever.retrieve("Binary Search comparisons for 1024 elements", top_k=2)
        assert len(retrieved) > 0
        top_chunk = retrieved[0][0]
        assert "Binary Search" in top_chunk["content"] or "1024" in top_chunk["content"]

        # Generate tutor response
        resp = GroundedTutor.generate_grounded_response(
            query="How many comparisons does Binary Search need for 1024 elements?",
            retrieved_items=retrieved,
            depth="intermediate",
            allow_outside=False
        )
        assert resp["is_grounded"] is True
        assert resp["refused"] is False
        assert len(resp["citations"]) >= 1
        top_cit = resp["citations"][0]
        assert top_cit["page_number"] == 3
        assert "cs101_algorithms_textbook.pdf" in top_cit["source_name"]
    finally:
        db.close()
