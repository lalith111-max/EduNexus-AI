import uuid
from typing import List, Dict, Any, Optional
from app.assessment.validator import AssessmentValidator
from app.schemas.assessment import QuestionSchema
from app.schemas.chat import Citation

class AssessmentEngine:
    """
    Adaptive Assessment Generator and Curator.
    Selects and validates questions tailored to the student's current BKT topic mastery.
    """

    @staticmethod
    def select_adaptive_questions(
        candidate_questions: List[Dict[str, Any]],
        student_mastery_p_l: float,
        num_questions: int = 5,
        target_topic: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Dynamically filters and ranks questions to maximize learning efficiency:
        - If student mastery < 0.40 -> Focus on easy/foundational questions (Zone of Proximal Development)
        - If student mastery 0.40 - 0.75 -> Balanced medium difficulty questions
        - If student mastery > 0.75 -> Challenge questions (hard/numerical)
        """
        filtered = candidate_questions
        if target_topic:
            filtered = [q for q in filtered if q.get("topic", "").lower() == target_topic.lower()]

        if not filtered:
            filtered = candidate_questions

        # Group by difficulty
        easy_qs = [q for q in filtered if q.get("difficulty") == "easy"]
        med_qs = [q for q in filtered if q.get("difficulty") == "medium"]
        hard_qs = [q for q in filtered if q.get("difficulty") == "hard"]

        selected = []
        if student_mastery_p_l < 0.40:
            # Low mastery: 60% easy, 40% medium
            selected.extend(easy_qs[:max(1, int(num_questions * 0.6))])
            remaining = num_questions - len(selected)
            selected.extend(med_qs[:remaining])
        elif student_mastery_p_l <= 0.75:
            # Intermediate: 20% easy, 60% medium, 20% hard
            selected.extend(med_qs[:max(1, int(num_questions * 0.6))])
            remaining = num_questions - len(selected)
            selected.extend(hard_qs[:max(1, int(remaining * 0.5))])
            remaining = num_questions - len(selected)
            selected.extend(easy_qs[:remaining])
        else:
            # High mastery: 60% hard, 40% medium
            selected.extend(hard_qs[:max(1, int(num_questions * 0.6))])
            remaining = num_questions - len(selected)
            selected.extend(med_qs[:remaining])

        # If pool was small, top up with any available questions
        if len(selected) < num_questions:
            seen_ids = {q["id"] for q in selected}
            for q in filtered:
                if q["id"] not in seen_ids:
                    selected.append(q)
                    seen_ids.add(q["id"])
                    if len(selected) >= num_questions:
                        break

        return selected[:num_questions]
