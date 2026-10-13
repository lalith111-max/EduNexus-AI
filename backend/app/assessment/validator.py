import re
import math
from typing import List, Dict, Any, Tuple, Optional

class AssessmentValidator:
    """
    Validates question integrity, recomputes numerical solutions programmatically,
    and checks for duplicate questions using lexical and n-gram similarity.
    """

    @staticmethod
    def validate_mcq(question_text: str, options: List[str], correct_answer: str) -> Tuple[bool, str]:
        if not question_text or len(question_text.strip()) < 10:
            return False, "Question text is too short or empty."
        
        if not options or len(options) < 2:
            return False, "MCQ must have at least 2 distinct options."
        
        # Check for duplicate options
        clean_opts = [o.strip().lower() for o in options]
        if len(set(clean_opts)) != len(clean_opts):
            return False, "MCQ contains duplicate options."
            
        # Check that correct_answer matches one of the options
        matches = [o for o in options if o.strip().lower() == correct_answer.strip().lower()]
        if len(matches) != 1:
            return False, f"Correct answer '{correct_answer}' must match exactly one option."
            
        return True, "Valid MCQ."

    @staticmethod
    def recalculate_numerical(formula: str, variables: Dict[str, float], expected_answer: float, tolerance: float = 0.01) -> Tuple[bool, float, str]:
        """
        Safely evaluates mathematical expressions and verifies expected answer.
        """
        allowed_names = {
            "math": math,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "pow": pow,
            "sqrt": math.sqrt,
            "log": math.log,
            "log2": math.log2,
            "exp": math.exp
        }
        allowed_names.update(variables)

        try:
            # Basic sanity check on formula string to prevent code injection
            if re.search(r"(__|import|eval|exec|open|os|sys)", formula):
                return False, expected_answer, "Formula contains disallowed keywords."

            calculated_value = float(eval(formula, {"__builtins__": {}}, allowed_names))
            is_valid = abs(calculated_value - expected_answer) <= (abs(expected_answer) * tolerance + 1e-6)
            
            if is_valid:
                return True, calculated_value, f"Calculated value {calculated_value} matches within tolerance {tolerance}."
            else:
                return False, calculated_value, f"Calculated value {calculated_value} does not match expected {expected_answer}."
        except Exception as e:
            return False, expected_answer, f"Evaluation error: {str(e)}"

    @staticmethod
    def check_duplicate(new_question_text: str, existing_questions: List[str], threshold: float = 0.80) -> Tuple[bool, float]:
        """
        Calculates character 3-gram Jaccard similarity between questions.
        Returns (is_duplicate, max_similarity).
        """
        def get_ngrams(text: str, n: int = 3) -> set:
            clean = re.sub(r"[^a-zA-Z0-9]", "", text.lower())
            if len(clean) < n:
                return {clean}
            return {clean[i:i+n] for i in range(len(clean) - n + 1)}

        new_grams = get_ngrams(new_question_text)
        if not new_grams:
            return False, 0.0

        max_sim = 0.0
        for existing in existing_questions:
            exist_grams = get_ngrams(existing)
            if not exist_grams:
                continue
            intersection = len(new_grams & exist_grams)
            union = len(new_grams | exist_grams)
            sim = (intersection / union) if union > 0 else 0.0
            if sim > max_sim:
                max_sim = sim

        is_dup = max_sim >= threshold
        return is_dup, max_sim
