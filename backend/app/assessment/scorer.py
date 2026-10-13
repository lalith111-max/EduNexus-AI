import re
from typing import List, Dict, Any, Tuple
from app.schemas.assessment import QuestionResult, MisconceptionReport
from app.schemas.chat import Citation

class AssessmentScorer:
    """
    Evaluates assessment responses, calculates scores,
    and isolates topic-level misconceptions grounded in source documents.
    """

    @staticmethod
    def score_attempt(
        questions: List[Dict[str, Any]],
        user_answers: Dict[str, str]
    ) -> Tuple[List[QuestionResult], List[MisconceptionReport], float, float]:
        """
        Returns (question_results, misconceptions, total_score, max_score).
        """
        results: List[QuestionResult] = []
        misconceptions: List[MisconceptionReport] = []
        total_score = 0.0
        max_score = float(len(questions))

        for q in questions:
            q_id = q["id"]
            q_text = q["question_text"]
            q_type = q.get("question_type", "mcq")
            correct_ans = str(q.get("correct_answer", "")).strip()
            explanation = q.get("explanation", "")
            topic = q.get("topic", "General")
            citations_raw = q.get("citations", [])
            citations = [Citation(**c) if isinstance(c, dict) else c for c in citations_raw]
            
            user_ans = str(user_answers.get(q_id, "")).strip()
            is_correct = False
            points = 0.0
            misconception_text = None
            remedial_excerpt = None

            # Scoring based on question type
            if q_type == "mcq":
                if user_ans.lower() == correct_ans.lower():
                    is_correct = True
                    points = 1.0
                else:
                    is_correct = False
                    points = 0.0
                    misconception_text = f"Selected '{user_ans}' instead of '{correct_ans}'. Review the fundamental distinction."
            
            elif q_type == "numerical":
                tolerance = float(q.get("tolerance", 0.01))
                try:
                    user_val = float(re.findall(r"[-+]?(?:\d*\.\d+|\d+)", user_ans)[0])
                    correct_val = float(re.findall(r"[-+]?(?:\d*\.\d+|\d+)", correct_ans)[0])
                    if abs(user_val - correct_val) <= (abs(correct_val) * tolerance + 1e-4):
                        is_correct = True
                        points = 1.0
                    else:
                        is_correct = False
                        points = 0.0
                        misconception_text = f"Numerical value {user_val} differs from verified solution {correct_val} (tolerance {tolerance})."
                except Exception:
                    is_correct = False
                    points = 0.0
                    misconception_text = "Input could not be parsed as a valid numerical solution."

            else:  # short_answer
                # Check for key tokens in rubric or explanation
                key_terms = [t.lower() for t in re.findall(r"\b[a-zA-Z]{4,}\b", correct_ans)]
                matched_terms = [t for t in key_terms if t in user_ans.lower()]
                overlap_ratio = len(matched_terms) / len(key_terms) if key_terms else 0.0

                if user_ans.lower() == correct_ans.lower() or overlap_ratio >= 0.5:
                    is_correct = True
                    points = 1.0
                elif overlap_ratio >= 0.25:
                    is_correct = False
                    points = 0.5
                    misconception_text = "Partially captured core concepts, but missed key definitions."
                else:
                    is_correct = False
                    points = 0.0
                    misconception_text = "Response did not cover the essential course concepts."

            total_score += points

            if not is_correct:
                first_cit = citations[0] if citations else None
                remedial_excerpt = first_cit.excerpt if first_cit else None
                misconceptions.append(MisconceptionReport(
                    topic=topic,
                    concept=q.get("concept_id") or topic,
                    misconception_text=misconception_text or "Concept misunderstanding identified.",
                    evidence_reasoning=f"Question: {q_text}\nExpected: {correct_ans}\nActual: {user_ans}",
                    remedial_source_citation=first_cit
                ))

            results.append(QuestionResult(
                question_id=q_id,
                question_text=q_text,
                question_type=q_type,
                topic=topic,
                user_answer=user_ans,
                correct_answer=correct_ans,
                is_correct=is_correct,
                points_earned=points,
                max_points=1.0,
                explanation=explanation,
                citations=citations,
                misconception=misconception_text,
                remedial_excerpt=remedial_excerpt
            ))

        return results, misconceptions, total_score, max_score
