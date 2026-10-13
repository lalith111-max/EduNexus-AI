import math
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple

class BayesianKnowledgeTracing:
    """
    Standard Bayesian Knowledge Tracing (BKT) implementation with mathematically
    exact posterior conditioning, learning transition, forgetting curve decay,
    and uncertainty estimation.
    """

    DEFAULT_P_L0 = 0.20  # Initial mastery prior
    DEFAULT_P_T = 0.15   # Transition / learning rate
    DEFAULT_P_G = 0.25   # Guess rate
    DEFAULT_P_S = 0.10   # Slip rate
    DEFAULT_DECAY_LAMBDA = 0.02  # Ebbinghaus forgetting rate per day

    @classmethod
    def compute_posterior(
        cls,
        p_l: float,
        is_correct: bool,
        p_g: float = DEFAULT_P_G,
        p_s: float = DEFAULT_P_S
    ) -> float:
        """
        Calculates P(L_t | Observation):
        If Correct:
          P(L_t | Correct) = [P(L_t)*(1 - P(S))] / [P(L_t)*(1 - P(S)) + (1 - P(L_t))*P(G)]
        If Incorrect:
          P(L_t | Incorrect) = [P(L_t)*P(S)] / [P(L_t)*P(S) + (1 - P(L_t))*(1 - P(G))]
        """
        p_l = max(0.001, min(0.999, p_l))

        if is_correct:
            num = p_l * (1.0 - p_s)
            den = (p_l * (1.0 - p_s)) + ((1.0 - p_l) * p_g)
        else:
            num = p_l * p_s
            den = (p_l * p_s) + ((1.0 - p_l) * (1.0 - p_g))

        posterior = num / den if den > 0 else p_l
        return max(0.001, min(0.999, posterior))

    @classmethod
    def compute_transition(cls, posterior_p_l: float, p_t: float = DEFAULT_P_T) -> float:
        """
        Calculates P(L_{t+1}) after learning opportunity:
        P(L_{t+1}) = Posterior + (1 - Posterior) * P(T)
        """
        p_next = posterior_p_l + (1.0 - posterior_p_l) * p_t
        return max(0.001, min(0.999, p_next))

    @classmethod
    def apply_forgetting(cls, p_l: float, elapsed_days: float, decay_lambda: float = DEFAULT_DECAY_LAMBDA) -> float:
        """
        Applies exponential forgetting decay:
        P(L) = P(L) * e^(-lambda * dt)
        """
        if elapsed_days <= 0:
            return p_l
        decay_factor = math.exp(-decay_lambda * elapsed_days)
        # Keep a floor at initial prior
        return max(cls.DEFAULT_P_L0 * 0.5, p_l * decay_factor)

    @classmethod
    def compute_uncertainty(cls, p_l: float, total_attempts: int) -> float:
        """
        Computes standard error / uncertainty band:
        SE = sqrt( P(L) * (1 - P(L)) / (N + 1) )
        """
        variance = (p_l * (1.0 - p_l)) / max(1, total_attempts + 1)
        return math.sqrt(variance)

    @classmethod
    def update_mastery(
        cls,
        current_p_l: float,
        is_correct: bool,
        total_attempts: int,
        p_t: float = DEFAULT_P_T,
        p_g: float = DEFAULT_P_G,
        p_s: float = DEFAULT_P_S
    ) -> Tuple[float, float, float]:
        """
        Full BKT step:
        Returns (prior_p_l, posterior_p_l, next_p_l, new_uncertainty)
        """
        posterior = cls.compute_posterior(current_p_l, is_correct, p_g=p_g, p_s=p_s)
        next_p_l = cls.compute_transition(posterior, p_t=p_t)
        new_uncertainty = cls.compute_uncertainty(next_p_l, total_attempts + 1)
        return next_p_l, posterior, new_uncertainty

    @staticmethod
    def get_mastery_label(p_l: float) -> str:
        if p_l < 0.40:
            return "needs_attention"
        elif p_l <= 0.75:
            return "improving"
        else:
            return "mastered"
