import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "EduNexus AI"
    assert "demo_mode" in data

def test_courses_and_knowledge_map():
    # 1. Get courses
    res = client.get("/api/courses")
    assert res.status_code == 200
    courses = res.json()
    assert len(courses) >= 2
    cs101 = next((c for c in courses if c["id"] == "course_cs101"), None)
    assert cs101 is not None

    # 2. Get topics
    res_topics = client.get("/api/courses/course_cs101/topics")
    assert res_topics.status_code == 200
    topics_data = res_topics.json()
    assert len(topics_data["topics"]) >= 3

    # 3. Get knowledge map
    res_map = client.get("/api/courses/course_cs101/knowledge-map")
    assert res_map.status_code == 200
    km = res_map.json()
    assert len(km["nodes"]) >= 4
    assert len(km["edges"]) >= 3

def test_sources_and_chunks():
    res = client.get("/api/sources?course_id=course_cs101")
    assert res.status_code == 200
    sources = res.json()
    assert len(sources) >= 1
    pdf_source = next((s for s in sources if s["source_type"] == "pdf"), None)
    assert pdf_source is not None
    assert pdf_source["page_count"] == 4

    # Check chunks endpoint
    res_chunks = client.get(f"/api/sources/{pdf_source['id']}/chunks")
    assert res_chunks.status_code == 200
    chunks = res_chunks.json()
    assert len(chunks) >= 4
    assert any(c["page_number"] == 1 for c in chunks)
    assert any(c["page_number"] == 2 for c in chunks)

def test_tutor_chat_grounded_and_refusal():
    # 1. Grounded query
    req = {
        "course_id": "course_cs101",
        "message": "What is the worst-case time complexity of QuickSort?",
        "depth": "intermediate",
        "allow_outside_knowledge": False
    }
    res = client.post("/api/tutor/chat", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["is_grounded"] is True
    assert data["refused"] is False
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["page_number"] == 2

    # 2. Unsupported query (must refuse)
    unsupported_req = {
        "course_id": "course_cs101",
        "message": "What is the secret recipe for baking artisanal sourdough bread?",
        "depth": "intermediate",
        "allow_outside_knowledge": False
    }
    res_unsupported = client.post("/api/tutor/chat", json=unsupported_req)
    assert res_unsupported.status_code == 200
    unsupp_data = res_unsupported.json()
    assert unsupp_data["refused"] is True
    assert unsupp_data["is_grounded"] is False
    assert len(unsupp_data["citations"]) == 0

def test_assessment_flow_and_mastery():
    # 1. Generate adaptive quiz
    gen_req = {
        "course_id": "course_cs101",
        "mode": "practice",
        "num_questions": 3
    }
    res_gen = client.post("/api/assessments/generate", json=gen_req)
    assert res_gen.status_code == 200
    asmt = res_gen.json()
    assert asmt["total_questions"] >= 2
    asmt_id = asmt["id"]

    # 2. Submit quiz answers
    first_q = asmt["questions"][0]
    submit_req = {
        "student_id": "default_student",
        "time_spent_secs": 45,
        "answers": [
            {"question_id": first_q["id"], "answer": "O(n^2) when the pivot is consistently the minimum or maximum element"}
        ]
    }
    res_sub = client.post(f"/api/assessments/{asmt_id}/submit", json=submit_req)
    assert res_sub.status_code == 200
    res_data = res_sub.json()
    assert "score" in res_data
    assert "accuracy" in res_data
    assert "mastery_deltas" in res_data

def test_learner_mastery_and_revision_plan():
    res_m = client.get("/api/mastery?course_id=course_cs101&student_id=default_student")
    assert res_m.status_code == 200
    m_data = res_m.json()
    assert "overall_mastery" in m_data
    assert len(m_data["topics"]) >= 3

    res_rec = client.get("/api/recommendations?course_id=course_cs101&student_id=default_student")
    assert res_rec.status_code == 200
    recs = res_rec.json()
    assert len(recs) >= 1

    res_rev = client.get("/api/revision-plan?course_id=course_cs101&student_id=default_student")
    assert res_rev.status_code == 200
    rev_data = res_rev.json()
    assert "weak_topic_flashcards" in rev_data
    assert "formula_cheat_sheets" in rev_data

def test_evaluation_benchmark_run():
    res_eval = client.post("/api/evaluation/run?course_id=course_cs101")
    assert res_eval.status_code == 200
    eval_data = res_eval.json()
    metrics = eval_data["metrics"]
    assert metrics["faithfulness"] >= 0.70
    assert metrics["citation_validity_rate"] >= 0.90
    assert metrics["refusal_accuracy"] >= 0.90
    assert "simulated_cohort_results" in eval_data
