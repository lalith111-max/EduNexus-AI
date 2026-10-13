import datetime
from typing import List, Dict, Any, Optional
from app.learner.bkt import BayesianKnowledgeTracing

class LearnerRecommender:
    """
    Intelligent recommendation engine driving personalized study paths,
    remedial action plans, and source-grounded revision materials.
    """

    @staticmethod
    def generate_recommendations(
        topic_masteries: List[Dict[str, Any]],
        prerequisite_edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Orders recommendations prioritizing:
        1. Weak topics that block downstream prerequisites
        2. Topics with high uncertainty or overdue review
        3. Mastery reinforcement for intermediate topics
        """
        recommendations = []
        mastery_map = {t["topic"]: t["p_l"] for t in topic_masteries}

        # Find prerequisite blockers
        blockers = set()
        for edge in prerequisite_edges:
            prereq = edge.get("prereq_topic") or edge.get("prereq_concept_id")
            target = edge.get("target_topic") or edge.get("target_concept_id")
            if prereq in mastery_map and mastery_map[prereq] < 0.50:
                blockers.add((prereq, target))

        # Check each topic
        for item in topic_masteries:
            topic = item["topic"]
            p_l = item["p_l"]
            attempts = item.get("total_attempts", 0)

            # Check if this topic blocks others
            is_blocker = any(b[0] == topic for b in blockers)

            if p_l < 0.40:
                priority = "high"
                if is_blocker:
                    reason = f"Critical Prerequisite: Low mastery ({p_l:.0%}) blocks progress in advanced concepts."
                else:
                    reason = f"Needs Attention: Current mastery is low ({p_l:.0%}) across {attempts} attempts."
                rec_type = "concept_review"
            elif p_l <= 0.75:
                priority = "medium"
                reason = f"Improving: Practice targeted problems to push mastery ({p_l:.0%}) past 80%."
                rec_type = "practice_quiz"
            else:
                priority = "low"
                reason = f"Mastered ({p_l:.0%}): Schedule spaced repetition check to prevent forgetting decay."
                rec_type = "revision"

            recommendations.append({
                "id": f"rec_{topic.lower().replace(' ', '_')}",
                "type": rec_type,
                "topic": topic,
                "title": f"Review & Practice: {topic}",
                "reason": reason,
                "mastery_score": round(p_l, 2),
                "priority": priority,
                "prerequisite_blocker": "Yes" if is_blocker else None
            })

        # Sort: high priority first, then lowest mastery
        priority_weights = {"high": 3, "medium": 2, "low": 1}
        recommendations.sort(key=lambda x: (priority_weights[x["priority"]], -x["mastery_score"]), reverse=True)
        return recommendations

    @staticmethod
    def generate_revision_materials(chunks: List[Dict[str, Any]], topic_masteries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extracts source-grounded flashcards, formula sheets, and summary points from indexed chunks.
        """
        flashcards = []
        formula_sheets = []
        quick_notes = []

        seen_terms = set()
        for c in chunks:
            content = c.get("content", "")
            source_name = c.get("source_name", "")
            loc = f"Page {c.get('page_number')}" if c.get("page_number") else (f"Slide {c.get('slide_number')}" if c.get("slide_number") else "Notes")
            citation_str = f"{source_name} ({loc})"

            # Extract formulas
            if "O(" in content or "=" in content or "formula" in content.lower():
                formula_lines = [line.strip() for line in content.splitlines() if any(k in line for k in ["O(", " = ", "sum", "formula", "log"])]
                for fl in formula_lines[:2]:
                    if len(fl) > 10 and len(fl) < 120 and fl not in seen_terms:
                        seen_terms.add(fl)
                        formula_sheets.append({
                            "title": fl.split(":")[0] if ":" in fl else "Core Formula",
                            "formula": fl,
                            "topic": c.get("concept_tags", ["General"])[0] if c.get("concept_tags") else "General",
                            "source_reference": citation_str
                        })

            # Extract flashcards
            if "is " in content or "defined as" in content.lower():
                sentences = [s.strip() for s in content.split(". ") if len(s) > 25]
                for s in sentences[:2]:
                    if s not in seen_terms:
                        seen_terms.add(s)
                        parts = s.split(" is ")
                        if len(parts) == 2:
                            flashcards.append({
                                "front": f"What is {parts[0].strip()}?",
                                "back": f"{parts[1].strip()}.",
                                "topic": c.get("concept_tags", ["General"])[0] if c.get("concept_tags") else "General",
                                "source_reference": citation_str
                            })
                        else:
                            flashcards.append({
                                "front": f"Explain: {s[:50]}...",
                                "back": s,
                                "topic": c.get("concept_tags", ["General"])[0] if c.get("concept_tags") else "General",
                                "source_reference": citation_str
                            })

            # Quick notes
            if len(quick_notes) < 8 and len(content) > 60:
                first_bullet = content.splitlines()[0]
                quick_notes.append({
                    "summary": first_bullet[:160] + "...",
                    "topic": c.get("concept_tags", ["General"])[0] if c.get("concept_tags") else "General",
                    "source_reference": citation_str
                })

        return {
            "flashcards": flashcards[:12],
            "formula_sheets": formula_sheets[:8],
            "quick_notes": quick_notes[:8]
        }
