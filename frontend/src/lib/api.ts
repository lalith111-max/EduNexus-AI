const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export interface Course {
  id: string;
  title: string;
  code: string;
  description: string;
  created_at: string;
}

export interface Citation {
  citation_id: string;
  source_id: string;
  source_name: string;
  source_type: string;
  chunk_id: string;
  page_number?: number;
  slide_number?: number;
  timestamp_start?: number;
  timestamp_end?: number;
  excerpt: string;
  relevance_score: number;
  verification_status: string;
}

export interface SourceItem {
  id: string;
  course_id: string;
  filename: string;
  source_type: string;
  content_hash: string;
  status: string;
  error_message?: string;
  extraction_method: string;
  page_count?: number;
  slide_count?: number;
  duration_seconds?: number;
  chunk_count: number;
  created_at: string;
}

export interface ChunkItem {
  chunk_id: string;
  course_id: string;
  source_id: string;
  source_name: string;
  source_type: string;
  content: string;
  page_number?: number;
  slide_number?: number;
  timestamp_start?: number;
  timestamp_end?: number;
  heading_path: string[];
  concept_tags: string[];
  extraction_method: string;
  confidence: number;
}

export interface KnowledgeNode {
  id: string;
  name: string;
  topic: string;
  category: string;
  difficulty: string;
  description: string;
  source_chunk_count: number;
}

export interface KnowledgeEdge {
  id: string;
  source: string;
  target: string;
  relationship: string;
  weight: number;
}

export interface KnowledgeMapData {
  course_id: string;
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
}

export interface TutorChatResponse {
  conversation_id: string;
  message_id: string;
  content: string;
  citations: Citation[];
  is_grounded: boolean;
  refused: boolean;
  refusal_reason?: string;
  outside_knowledge_used: boolean;
  confidence_score: number;
  retrieved_chunks_count: number;
}

export interface QuestionPublic {
  id: string;
  topic: string;
  question_text: string;
  question_type: string;
  difficulty: string;
  options?: string[];
  citations: Citation[];
}

export interface AssessmentData {
  id: string;
  course_id: string;
  title: string;
  mode: string;
  topic?: string;
  time_limit_mins: number;
  questions: QuestionPublic[];
  total_questions: number;
  created_at: string;
}

export interface QuestionResult {
  question_id: string;
  question_text: string;
  question_type: string;
  topic: string;
  user_answer: string;
  correct_answer: string;
  is_correct: boolean;
  points_earned: number;
  max_points: number;
  explanation: string;
  citations: Citation[];
  misconception?: string;
  remedial_excerpt?: string;
}

export interface MisconceptionReport {
  topic: string;
  concept: string;
  misconception_text: string;
  evidence_reasoning: string;
  remedial_source_citation?: Citation;
}

export interface AssessmentResultData {
  attempt_id: string;
  assessment_id: string;
  student_id: string;
  score: number;
  total_points: number;
  accuracy: number;
  time_spent_secs: number;
  question_results: QuestionResult[];
  misconceptions: MisconceptionReport[];
  mastery_deltas: Record<string, { prior: number; posterior: number; delta: number }>;
  weak_topics: string[];
  recommended_next_action: string;
  completed_at: string;
}

export interface TopicMastery {
  id: string;
  student_id: string;
  course_id: string;
  topic: string;
  p_l: number;
  p_t: number;
  p_g: number;
  p_s: number;
  uncertainty: number;
  total_attempts: number;
  correct_attempts: number;
  streak: number;
  mastery_status: string;
  last_practiced: string;
  next_review_at: string;
  history: number[];
}

export interface LearnerOverview {
  student_id: string;
  course_id: string;
  overall_mastery: number;
  total_attempts: number;
  average_accuracy: number;
  topics: TopicMastery[];
  strongest_topics: string[];
  weakest_topics: string[];
  recent_streak_days: number;
  due_reviews_count: number;
}

export interface RecommendationItem {
  id: string;
  type: string;
  topic: string;
  title: string;
  reason: string;
  mastery_score: number;
  priority: string;
  prerequisite_blocker?: string;
}

export interface RevisionPlanData {
  student_id: string;
  course_id: string;
  target_exam_date?: string;
  daily_study_mins: number;
  schedule_recommendations: Array<{ day: string; focus: string; estimated_mins: number; status: string }>;
  weak_topic_flashcards: Array<{ front: string; back: string; topic: string; source_reference: string }>;
  formula_cheat_sheets: Array<{ title: string; formula: string; topic: string; source_reference: string }>;
  quick_revision_notes: Array<{ summary: string; topic: string; source_reference: string }>;
}

export interface EvalRunData {
  run_id: string;
  run_name: string;
  timestamp: string;
  metrics: {
    faithfulness: number;
    answer_relevancy: number;
    context_precision: number;
    context_recall: number;
    citation_validity_rate: number;
    refusal_accuracy: number;
    latency_ms_avg: number;
    total_test_cases: number;
  };
  test_case_results: Array<any>;
  simulated_cohort_results?: any;
}

// API Helper
async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorBody.detail || `Request failed: ${res.status}`);
  }

  return res.json();
}

export const api = {
  // Health
  getHealth: () => request<{ status: string; service: string; demo_mode: boolean }>("/health"),

  // Courses
  getCourses: () => request<Course[]>("/courses"),
  getKnowledgeMap: (courseId: string) => request<KnowledgeMapData>(`/courses/${courseId}/knowledge-map`),
  getTopics: (courseId: string) => request<{ topics: string[] }>(`/courses/${courseId}/topics`),

  // Sources
  getSources: (courseId: string) => request<SourceItem[]>(`/sources?course_id=${courseId}`),
  getSourceChunks: (sourceId: string) => request<ChunkItem[]>(`/sources/${sourceId}/chunks`),
  deleteSource: (sourceId: string) => request<{ message: string }>(`/sources/${sourceId}`, { method: "DELETE" }),
  uploadSource: async (courseId: string, file: File): Promise<SourceItem> => {
    const formData = new FormData();
    formData.append("course_id", courseId);
    formData.append("file", file);

    const res = await fetch(`${API_BASE_URL}/sources/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Upload failed");
    }
    return res.json();
  },

  // Tutor
  sendTutorChat: (data: {
    course_id: string;
    message: string;
    depth?: string;
    topic_filter?: string;
    allow_outside_knowledge?: boolean;
    conversation_id?: string;
  }) =>
    request<TutorChatResponse>("/tutor/chat", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Assessments
  generateAssessment: (data: {
    course_id: string;
    topic?: string;
    mode?: string;
    num_questions?: number;
  }) =>
    request<AssessmentData>("/assessments/generate", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getAssessment: (id: string) => request<AssessmentData>(`/assessments/${id}`),
  submitAssessment: (
    id: string,
    data: {
      student_id?: string;
      time_spent_secs: number;
      answers: Array<{ question_id: string; answer: string }>;
    }
  ) =>
    request<AssessmentResultData>(`/assessments/${id}/submit`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Mastery & Revision
  getMastery: (courseId: string, studentId: string = "default_student") =>
    request<LearnerOverview>(`/mastery?course_id=${courseId}&student_id=${studentId}`),
  getRecommendations: (courseId: string, studentId: string = "default_student") =>
    request<RecommendationItem[]>(`/recommendations?course_id=${courseId}&student_id=${studentId}`),
  getRevisionPlan: (courseId: string, studentId: string = "default_student") =>
    request<RevisionPlanData>(`/revision-plan?course_id=${courseId}&student_id=${studentId}`),

  // Evaluation
  runEvaluation: (courseId: string = "course_cs101") =>
    request<EvalRunData>(`/evaluation/run?course_id=${courseId}`, { method: "POST" }),
  getEvaluationResults: () => request<EvalRunData[]>("/evaluation/results"),
};
