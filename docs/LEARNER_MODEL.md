# EduNexus AI - Learner Model & Adaptive Personalization

EduNexus AI employs an interpretable, mathematically sound **Bayesian Knowledge Tracing (BKT)** model to estimate topic-wise student mastery across sessions.

---

## 1. Mathematical Formulation

Bayesian Knowledge Tracing assumes that student mastery on a given concept is a latent binary state $L_t \in \{0, 1\}$ (Unmastered or Mastered). At each evaluation opportunity, we observe an outcome $Obs_t \in \{\text{Correct}, \text{Incorrect}\}$.

### Model Hyperparameters
- $P(L_0) = 0.20$: Prior probability of knowing the skill initially.
- $P(T) = 0.15$: Probability of learning transition (transitioning from unmastered to mastered on practice).
- $P(G) = 0.25$: Guess probability (probability of answering correctly without knowing the concept, standard for 4-option MCQs).
- $P(S) = 0.10$: Slip probability (probability of making an error despite possessing mastery).

### Posterior Update Given Observation
Upon receiving observation $Obs_t$:

**Case 1: Observation is Correct**
$$P(L_t \mid \text{Correct}) = \frac{P(L_t)(1 - P(S))}{P(L_t)(1 - P(S)) + (1 - P(L_t))P(G)}$$

**Case 2: Observation is Incorrect**
$$P(L_t \mid \text{Incorrect}) = \frac{P(L_t)P(S)}{P(L_t)P(S) + (1 - P(L_t))(1 - P(G))}$$

### Learning Transition Update
Following practice opportunity $t$, mastery transition is computed for opportunity $t+1$:
$$P(L_{t+1}) = P(L_t \mid Obs_t) + (1 - P(L_t \mid Obs_t)) \cdot P(T)$$

### Forgetting Curve Decay
Between practice sessions separated by elapsed time $\Delta t$ (days), an exponential decay discount is applied:
$$P(L_{\text{decayed}}) = P(L) \cdot e^{-\lambda \Delta t}$$
where default decay rate $\lambda = 0.02$ day$^{-1}$.

### Uncertainty Estimation
Uncertainty $\sigma$ is computed from the standard error of binomial knowledge estimation:
$$\sigma = \sqrt{\frac{P(L)(1 - P(L))}{N + 1}}$$
where $N$ is the cumulative number of practice attempts.

---

## 2. Mastery States & Color Representation

| Mastery Probability $P(L)$ | Status Label | Visual Representation | Recommended Action |
|:---|:---|:---|:---|
| $0.00 \le P(L) < 0.40$ | `needs_attention` | Amber / Rose (#f59e0b) | Foundational review, easy diagnostic practice |
| $0.40 \le P(L) \le 0.75$ | `improving` | Indigo (#6366f1) | Medium difficulty drills, MCQ concept reinforcement |
| $0.75 < P(L) \le 1.00$ | `mastered` | Emerald (#10b981) | Challenge synthesis, formula drills, spaced review |

---

## 3. Zone of Proximal Development (ZPD) Adaptive Question Selection

When generating quizzes, the assessment engine does not pick questions randomly. It adjusts problem difficulty based on the student's current $P(L)$:

- **Low Mastery ($P(L) < 0.40$)**: 60% easy questions, 40% medium questions to build fundamental confidence.
- **Intermediate Mastery ($0.40 \le P(L) \le 0.75$)**: 60% medium questions, 20% hard questions, 20% easy questions.
- **High Mastery ($P(L) > 0.75$)**: 60% hard / numerical multi-step questions, 40% medium questions.

---

## 4. Grounded Misconception Diagnosis
When a student answers incorrectly:
1. Distractor patterns are matched against common cognitive traps (e.g. confusing worst-case with average-case complexity).
2. The system identifies the specific conceptual gap.
3. Remedial links directly cite the exact page or slide where the correct theorem is taught.
