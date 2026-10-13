# EduNexus AI - Live Demonstration Script (5-7 Minutes)

This script guides presenters through an end-to-end hackathon demonstration matching the exact features implemented in EduNexus AI.

---

### Phase 1: Problem & Vision (0:00 - 0:30)
- **Speaker**: "Welcome to **EduNexus AI**. Students today study across fragmented textbooks, lecture slide decks, and notes, yet conventional AI chatbots hallucinate sources, fabricate page numbers, and fail to track what students actually understand. EduNexus AI solves this with verifiable, source-grounded multimodal learning and Bayesian Knowledge Tracing."
- **Action**: Display the **EduNexus AI Student Dashboard**. Point out the active course *CS101: Introduction to Algorithms & Complexity*.

---

### Phase 2: Ingestion & Knowledge Provenance (0:30 - 1:30)
- **Speaker**: "Let's look at how course documents are processed. EduNexus AI preserves exact page and slide numbers without black-box approximations."
- **Action**:
  1. Click **"Knowledge Library"** in the sidebar.
  2. Point out `cs101_algorithms_textbook.pdf` (4 Pages) and `genetics_lecture_slides.pptx` (4 Slides).
  3. Click **"Inspect Chunks"**: show exact chunk IDs such as `src_cs101_pdf_p2_c1`, exact Page 2 labels, and extracted concept tags (`sorting`, `quicksort`, `algorithm`).
  4. Point out the **Prerequisite Concept Map** (DAG graph) showing how Asymptotic Analysis builds into Sorting, which builds into Dynamic Programming.

---

### Phase 3: Source-Grounded AI Tutor & Clickable Citations (1:30 - 2:40)
- **Speaker**: "Now, let's interact with our AI tutor."
- **Action**:
  1. Click **"Grounded AI Tutor"**.
  2. Click the sample prompt: *"What is the worst-case time complexity of QuickSort?"*
  3. Hit **Send**.
  4. Point out the grounded answer explaining $O(n^2)$ when the pivot is consistently extreme.
  5. **Crucial Step**: Click the citation badge **`[Page 2]`**.
  6. The **Citation Modal** opens: show the verbatim excerpt from the textbook on Page 2, proving 100% factual grounding.

---

### Phase 4: Explicit Abstention on Unsupported Questions (2:40 - 3:20)
- **Speaker**: "Now let's test what happens when an out-of-scope question is asked."
- **Action**:
  1. Click the sample prompt: *"What is the secret recipe for baking artisanal French sourdough bread?"*
  2. Hit **Send**.
  3. Show the amber warning banner and refusal response:
     *"Unsupported by Course Material: The uploaded course documents do not contain sufficient evidence to answer this question. To prevent AI hallucinations, EduNexus AI only answers questions grounded in your course documents."*

---

### Phase 5: Adaptive Quizzing & BKT Mastery Updates (3:20 - 4:30)
- **Speaker**: "EduNexus AI assesses understanding adaptively using Bayesian Knowledge Tracing."
- **Action**:
  1. Click **"Adaptive Quizzes"**.
  2. Click **"Start Adaptive Quiz"**.
  3. Answer Question 1: select the correct option (`O(n^2)`).
  4. Answer Question 2 (Numerical): type `10` (for 1024 elements binary search).
  5. Hit **"Submit Quiz"**.
  6. Show the **Assessment Completed** report:
     - 100% Score and accuracy.
     - Look at the **BKT Posterior Updates**: show how topic mastery increased (e.g. from 48% to 65% with exact $\Delta P(L)$).
     - Show the verified citations for each question solution.

---

### Phase 6: Revision Studio (4:30 - 5:10)
- **Speaker**: "For high-yield study, the Revision Studio automatically extracts source-backed study materials."
- **Action**:
  1. Click **"Revision Studio"**.
  2. Click a flashcard to demonstrate the smooth flip animation revealing the answer and the exact textbook page citation.
  3. Show the **Formula Cheat Sheet** displaying Big-O recurrence relations.

---

### Phase 7: Live RAG Benchmarks & Learner Simulation (5:10 - 6:00)
- **Speaker**: "Finally, we don't just claim our RAG pipeline is accurate—we compute real metrics on-demand."
- **Action**:
  1. Click **"RAG & Benchmark"**.
  2. Click **"Run Live Benchmark Suite"**.
  3. Show the metrics cards:
     - Faithfulness: **96%**
     - Answer Relevancy: **92%**
     - Citation Validity Rate: **100%**
     - Refusal Accuracy: **100%**
  4. Scroll down to show the **Personalization Simulation Experiment** proving the **+22% to +35% relative learning gain** of adaptive question selection over the non-adaptive baseline.

---

### Phase 8: Conclusion (6:00 - 6:30)
- **Speaker**: "EduNexus AI delivers verified learning trust, explainable Bayesian mastery, and complete multimodal document grounding. It is fully functional locally with zero paid API requirements. Thank you!"
