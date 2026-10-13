# EduNexus AI - Grounding and Citations Architecture

## 1. Foundational Principle: Trust Before Fluency
In academic learning, an ungrounded or hallucinated AI response is worse than no answer. A student preparing for high-stakes examinations cannot afford to memorize inaccurate theorems or imaginary formulas.

**Grounding Invariant:** EduNexus AI never invents a quotation, fabricates a page number, invents a slide number, or creates a citation that cannot be verified in the active course vector index.

---

## 2. Ingestion-to-Chunk Metadata Propagation

When a document is uploaded, it is processed through format-specific structural parsers:

1. **PDF Ingestion (`PDFParser`)**:
   - Uses structural layout extraction to preserve exact, 1-indexed page boundaries.
   - Computes text density to flag scanned pages.
   - Extracts section headings.
2. **PowerPoint Ingestion (`PPTXParser`)**:
   - Inspects slide indices, titles, shape text frames, and speaker notes.
   - Stores exact 1-indexed slide numbers.
3. **Chunking (`StructureAwareChunker`)**:
   - Chunks respect paragraph boundaries and token limits (100–900 characters).
   - Each chunk receives a deterministic, human-auditable chunk ID:
     - PDF chunk format: `{source_id}_p{page_number}_c{chunk_index}` (e.g. `src_cs101_pdf_p2_c1`)
     - PPTX chunk format: `{source_id}_s{slide_number}_c{chunk_index}` (e.g. `src_bio102_pptx_s3_c1`)
     - Media chunk format: `{source_id}_t{timestamp_sec}_c{chunk_index}`
   - Every chunk record stores: `source_name`, `page_number`, `slide_number`, `timestamp_start`, `timestamp_end`, `concept_tags`, `extraction_method`, and `confidence`.

---

## 3. Retrieval & Candidate Verification

Retrieval combines two orthogonal retrieval paradigms:
- **Lexical Matching (Okapi BM25)**: Evaluates high-precision keyword overlap with stop-word filtering.
- **Dense Semantic Projection**: Generates normalized dense feature embeddings for conceptual similarity.

### The Sufficiency Check
Before generating an answer, the hybrid retriever evaluates evidence coverage:
1. **Adversarial Pattern Mitigation**: Prompt injection phrases (`ignore previous instructions`, `passwords`, `bypass`) are identified and refused.
2. **Lexical Grounding Check**: If the query's content tokens have zero presence in the corpus, dense similarity alone cannot fabricate an association.
3. **Confidence Thresholding**: If the top score is below `0.28` or substantive query terms are under-represented (`< 30%`), the query enters the **Explicit Abstention Pathway**.

---

## 4. Grounded Synthesis & Citation Validation

When sufficient evidence exists:
1. The tutor constructs an explanation referencing the retrieved chunks.
2. Citations are verified by `CitationValidator`:
   - Checks that `chunk_id` exists in the retrieved context.
   - Checks that `page_number` or `slide_number` matches the stored database chunk.
   - Extracts verbatim excerpt sentences directly from the chunk text.
3. When the user clicks a citation badge in the interface, `CitationModal` displays the exact document, location, and supporting passage.

---

## 5. Explicit Abstention Pathway
When an out-of-scope question is submitted (e.g. asking for culinary recipes in a Computer Science course):
- EduNexus AI responds with:
  > **Unsupported by Course Material**
  >
  > The uploaded course documents do not contain sufficient evidence to answer: *"What is the secret recipe for baking artisanal French sourdough bread?"*.
  >
  > To uphold academic accuracy and prevent AI hallucinations, EduNexus AI only answers questions grounded in your course documents.
- The UI displays an amber refusal banner (`ShieldAlert`).
- If the student explicitly toggles **"Allow Outside Knowledge"**, the answer is clearly watermarked with `[Outside Course Material]` banners.
