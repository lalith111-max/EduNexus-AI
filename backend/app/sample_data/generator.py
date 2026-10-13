import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from pptx import Presentation
from pptx.util import Inches, Pt
from app.core.config import SAMPLE_DATA_DIR

def generate_sample_pdf(output_path: Path):
    """
    Generates a genuine 4-page academic textbook chapter with exact page citations.
    """
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'ChapterTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=8
    )

    story = []

    # Page 1: Algorithm Complexity & Big-O Notation
    story.append(Paragraph("Chapter 1: Foundations of Algorithm Analysis", title_style))
    story.append(Paragraph("1.1 Asymptotic Notations and Big-O", heading_style))
    story.append(Paragraph(
        "Asymptotic analysis measures algorithm efficiency as input size n grows toward infinity. "
        "Big-O notation provides an asymptotic upper bound on worst-case execution time. Formally, "
        "f(n) = O(g(n)) if there exist positive constants c and n0 such that 0 <= f(n) <= c*g(n) for all n >= n0. "
        "Common complexity classes include O(1) constant time, O(log n) logarithmic, O(n) linear, "
        "O(n log n) linearithmic, and O(n^2) quadratic time.", body_style
    ))
    story.append(Paragraph(
        "Worst-case analysis guarantees the maximum running time for any input of size n. "
        "Average-case analysis computes expected execution time over a probability distribution of inputs. "
        "Best-case analysis identifies the fastest possible execution for favorable inputs.", body_style
    ))
    story.append(PageBreak())

    # Page 2: Divide and Conquer - Sorting Algorithms
    story.append(Paragraph("1.2 Divide-and-Conquer Paradigm", heading_style))
    story.append(Paragraph(
        "The divide-and-conquer paradigm breaks a computational problem into smaller, independent subproblems "
        "of the same type, solves them recursively, and combines their solutions. "
        "MergeSort divides the input array of size n into two halves of size n/2, recursively sorts each half, "
        "and merges the two sorted sequences in O(n) linear time. The recurrence relation is T(n) = 2T(n/2) + O(n), "
        "yielding a guaranteed worst-case time complexity of O(n log n). However, standard MergeSort requires "
        "O(n) auxiliary memory space to perform the merge operation.", body_style
    ))
    story.append(Paragraph(
        "QuickSort selects a pivot element and partitions the array into elements smaller than and larger than the pivot. "
        "In the average case with random pivots, QuickSort executes in O(n log n) time and operates in-place, requiring "
        "only O(log n) auxiliary stack space for recursion. In the worst case—when the pivot is consistently the minimum "
        "or maximum element, such as on an already sorted array—the recurrence becomes T(n) = T(n-1) + O(n), resulting in "
        "O(n^2) quadratic running time.", body_style
    ))
    story.append(PageBreak())

    # Page 3: Searching & Logarithmic Scaling
    story.append(Paragraph("1.3 Searching in Sorted Collections", heading_style))
    story.append(Paragraph(
        "Binary Search is an optimal search algorithm for sorted random-access sequences. At each step, "
        "the algorithm probes the median element at index mid = floor((low + high) / 2). "
        "If the target matches the median, search terminates successfully. If the target is smaller, "
        "the search continues in the left subarray; otherwise, it proceeds in the right subarray.", body_style
    ))
    story.append(Paragraph(
        "Because Binary Search eliminates half of the remaining candidate elements with each comparison, "
        "its recurrence relation is T(n) = T(n/2) + O(1). The maximum number of comparisons required for an "
        "array of size n is floor(log2(n)) + 1. For example, for an array with n = 1024 elements, Binary Search "
        "requires at most 10 comparisons, demonstrating exponential search-space reduction.", body_style
    ))
    story.append(PageBreak())

    # Page 4: Dynamic Programming & Overlapping Subproblems
    story.append(Paragraph("1.4 Dynamic Programming Foundations", heading_style))
    story.append(Paragraph(
        "Dynamic Programming (DP) is an algorithm design technique applied when a problem exhibits both "
        "optimal substructure and overlapping subproblems. Optimal substructure means that an optimal solution "
        "to the global problem contains optimal solutions to subproblems within it. "
        "Overlapping subproblems occur when the recursive space visits identical subproblems repeatedly.", body_style
    ))
    story.append(Paragraph(
        "Unlike Divide-and-Conquer which repeatedly resolves disjoint subproblems, Dynamic Programming stores "
        "the result of each solved subproblem in a lookup table. The two primary implementation strategies are "
        "top-down memoization (caching recursive call returns) and bottom-up tabulation (iteratively filling a table "
        "from base cases). A classic example is computing Fibonacci numbers: naive recursion requires O(2^n) exponential time, "
        "while dynamic programming achieves O(n) linear time with O(n) or O(1) space.", body_style
    ))

    doc.build(story)


def generate_sample_pptx(output_path: Path):
    """
    Generates a genuine 4-slide lecture presentation with exact slide provenance.
    """
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Slide 1: Molecular Biology & The Central Dogma
    slide1 = prs.slides.add_slide(blank_layout)
    txBox = slide1.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(8.4), Inches(1.2))
    tf = txBox.text_frame
    tf.text = "Lecture 3: Molecular Biology & The Central Dogma"
    p = tf.paragraphs[0]
    p.font.size = Pt(28)
    p.font.bold = True

    txBody = slide1.shapes.add_textbox(Inches(0.8), Inches(2.2), Inches(8.4), Inches(4.5))
    tfBody = txBody.text_frame
    p1 = tfBody.add_paragraph()
    p1.text = "• The Central Dogma of Molecular Biology describes the flow of genetic information: DNA -> RNA -> Protein."
    p1.font.size = Pt(16)
    p2 = tfBody.add_paragraph()
    p2.text = "• DNA (Deoxyribonucleic Acid) stores hereditary instructions in a double-helix composed of adenine, thymine, cytosine, and guanine."
    p2.font.size = Pt(16)
    p3 = tfBody.add_paragraph()
    p3.text = "• Base pairing rules: Adenine pairs with Thymine (A-T via 2 hydrogen bonds), Cytosine pairs with Guanine (C-G via 3 hydrogen bonds)."
    p3.font.size = Pt(16)

    # Slide 2: Transcription and Translation
    slide2 = prs.slides.add_slide(blank_layout)
    txBox2 = slide2.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(8.4), Inches(1.2))
    tf2 = txBox2.text_frame
    tf2.text = "Transcription & Protein Translation"
    tf2.paragraphs[0].font.size = Pt(28)
    tf2.paragraphs[0].font.bold = True

    txBody2 = slide2.shapes.add_textbox(Inches(0.8), Inches(2.2), Inches(8.4), Inches(4.5))
    tfBody2 = txBody2.text_frame
    p2_1 = tfBody2.add_paragraph()
    p2_1.text = "• Transcription: RNA polymerase synthesizes messenger RNA (mRNA) from a DNA template strand in the cell nucleus."
    p2_1.font.size = Pt(16)
    p2_2 = tfBody2.add_paragraph()
    p2_2.text = "• RNA replaces thymine with uracil; adenine in DNA binds to uracil in mRNA during transcript elongation."
    p2_2.font.size = Pt(16)
    p2_3 = tfBody2.add_paragraph()
    p2_3.text = "• Translation: Ribosomes translate mRNA codons (triplets of nucleotides) into amino acid polypeptide chains using tRNA transfer molecules."
    p2_3.font.size = Pt(16)

    # Slide 3: Cellular Respiration & ATP Yield
    slide3 = prs.slides.add_slide(blank_layout)
    txBox3 = slide3.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(8.4), Inches(1.2))
    tf3 = txBox3.text_frame
    tf3.text = "Bioenergetics: Cellular Respiration & ATP Yield"
    tf3.paragraphs[0].font.size = Pt(28)
    tf3.paragraphs[0].font.bold = True

    txBody3 = slide3.shapes.add_textbox(Inches(0.8), Inches(2.2), Inches(8.4), Inches(4.5))
    tfBody3 = txBody3.text_frame
    p3_1 = tfBody3.add_paragraph()
    p3_1.text = "• Cellular respiration converts biochemical energy from glucose into adenosine triphosphate (ATP)."
    p3_1.font.size = Pt(16)
    p3_2 = tfBody3.add_paragraph()
    p3_2.text = "• Glycolysis occurs in cytoplasm: 1 Glucose -> 2 Pyruvate + 2 net ATP + 2 NADH (anaerobic, no oxygen required)."
    p3_2.font.size = Pt(16)
    p3_3 = tfBody3.add_paragraph()
    p3_3.text = "• Krebs Cycle (Citric Acid Cycle) in mitochondrial matrix produces 2 ATP, 6 NADH, and 2 FADH2 per glucose."
    p3_3.font.size = Pt(16)
    p3_4 = tfBody3.add_paragraph()
    p3_4.text = "• Oxidative Phosphorylation on mitochondrial inner membrane produces ~26-28 ATP via ATP synthase, for total net yield of ~30-32 ATP."
    p3_4.font.size = Pt(16)

    # Slide 4: Mitosis vs Meiosis
    slide4 = prs.slides.add_slide(blank_layout)
    txBox4 = slide4.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(8.4), Inches(1.2))
    tf4 = txBox4.text_frame
    tf4.text = "Cell Division: Mitosis vs. Meiosis"
    tf4.paragraphs[0].font.size = Pt(28)
    tf4.paragraphs[0].font.bold = True

    txBody4 = slide4.shapes.add_textbox(Inches(0.8), Inches(2.2), Inches(8.4), Inches(4.5))
    tfBody4 = txBody4.text_frame
    p4_1 = tfBody4.add_paragraph()
    p4_1.text = "• Mitosis consists of one nuclear division producing 2 genetically identical diploid (2n) somatic cells for growth and tissue repair."
    p4_1.font.size = Pt(16)
    p4_2 = tfBody4.add_paragraph()
    p4_2.text = "• Meiosis consists of two successive nuclear divisions (Meiosis I and Meiosis II) producing 4 genetically diverse haploid (1n) gametes."
    p4_2.font.size = Pt(16)
    p4_3 = tfBody4.add_paragraph()
    p4_3.text = "• Genetic variation in meiosis results from homologous crossing over in Prophase I and independent assortment in Metaphase I."
    p4_3.font.size = Pt(16)

    prs.save(str(output_path))


def ensure_sample_files():
    pdf_path = SAMPLE_DATA_DIR / "cs101_algorithms_textbook.pdf"
    pptx_path = SAMPLE_DATA_DIR / "genetics_lecture_slides.pptx"
    notes_path = SAMPLE_DATA_DIR / "data_structures_notes.md"

    if not pdf_path.exists():
        generate_sample_pdf(pdf_path)

    if not pptx_path.exists():
        generate_sample_pptx(pptx_path)

    if not notes_path.exists():
        with open(notes_path, "w", encoding="utf-8") as f:
            f.write(
                "# Course Notes: Data Structures & Trees\n\n"
                "## Binary Search Trees (BST)\n"
                "A Binary Search Tree is a binary tree data structure where each node satisfies the BST invariant: "
                "the key in any node is strictly greater than all keys stored in its left subtree, and strictly less than "
                "or equal to all keys stored in its right subtree.\n\n"
                "In an average balanced BST, search, insertion, and deletion operate in O(log n) time. In the worst-case degenerate "
                "tree (a linked-list structure), these operations degrade to O(n) linear time.\n\n"
                "## Binary Heaps\n"
                "A binary heap is a complete binary tree that satisfies the heap property: in a max-heap, parent >= children; "
                "in a min-heap, parent <= children. Building a binary heap from an unsorted array takes O(n) linear time using "
                "Floyd's bottom-up heap construction algorithm.\n"
            )
