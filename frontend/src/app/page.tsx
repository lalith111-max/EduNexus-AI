"use client";

import React, { useState, useEffect } from "react";
import {
  api,
  Course,
  SourceItem,
  ChunkItem,
  Citation,
  TutorChatResponse,
  AssessmentData,
  AssessmentResultData,
  LearnerOverview,
  RecommendationItem,
  RevisionPlanData,
  EvalRunData,
  KnowledgeMapData,
} from "@/lib/api";
import { CitationModal } from "@/components/CitationModal";
import {
  BookOpen,
  BrainCircuit,
  GraduationCap,
  Sparkles,
  UploadCloud,
  Layers,
  BarChart3,
  CheckCircle2,
  AlertCircle,
  Clock,
  Send,
  RefreshCw,
  Search,
  Check,
  X,
  Play,
  RotateCcw,
  Zap,
  ShieldAlert,
  HelpCircle,
  FileText,
  Presentation,
  Award,
  ChevronRight,
  TrendingUp,
  Sliders,
  Database,
  Calendar,
  ExternalLink,
  Info,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart,
  Line,
  Legend,
  AreaChart,
  Area,
} from "recharts";

type NavTab =
  | "dashboard"
  | "tutor"
  | "assessment"
  | "library"
  | "upload"
  | "mastery"
  | "revision"
  | "evaluation"
  | "settings";

export default function EduNexusApp() {
  const [activeTab, setActiveTab] = useState<NavTab>("dashboard");
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<string>("course_cs101");
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Dashboard & Learner Data
  const [masteryData, setMasteryData] = useState<LearnerOverview | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);

  // Tutor state
  const [tutorQuery, setTutorQuery] = useState("");
  const [tutorDepth, setTutorDepth] = useState<string>("intermediate");
  const [allowOutsideKnowledge, setAllowOutsideKnowledge] = useState(false);
  const [chatMessages, setChatMessages] = useState<
    Array<{
      role: "user" | "assistant";
      content: string;
      citations?: Citation[];
      is_grounded?: boolean;
      refused?: boolean;
      outside_knowledge_used?: boolean;
    }>
  >([
    {
      role: "assistant",
      content:
        "Welcome to **EduNexus AI**. I am your source-grounded academic tutor. Ask me questions about your course materials, and I will provide answers with exact page, slide, and timestamp citations.",
    },
  ]);
  const [tutorLoading, setTutorLoading] = useState(false);

  // Assessment state
  const [currentAssessment, setCurrentAssessment] = useState<AssessmentData | null>(null);
  const [userAnswers, setUserAnswers] = useState<Record<string, string>>({});
  const [assessmentResult, setAssessmentResult] = useState<AssessmentResultData | null>(null);
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  const [selectedTopicForQuiz, setSelectedTopicForQuiz] = useState<string>("");

  // Library & Chunks
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [selectedSourceForChunks, setSelectedSourceForChunks] = useState<string | null>(null);
  const [inspectChunks, setInspectChunks] = useState<ChunkItem[]>([]);
  const [knowledgeMap, setKnowledgeMap] = useState<KnowledgeMapData | null>(null);

  // Revision state
  const [revisionPlan, setRevisionPlan] = useState<RevisionPlanData | null>(null);
  const [flippedCards, setFlippedCards] = useState<Record<number, boolean>>({});

  // Evaluation state
  const [evalRunData, setEvalRunData] = useState<EvalRunData | null>(null);
  const [evalLoading, setEvalLoading] = useState(false);

  // Upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(false);

  // Initialize and load data
  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (selectedCourseId) {
      loadCourseData(selectedCourseId);
    }
  }, [selectedCourseId]);

  const loadInitialData = async () => {
    try {
      const courseList = await api.getCourses();
      setCourses(courseList);
      if (courseList.length > 0 && !selectedCourseId) {
        setSelectedCourseId(courseList[0].id);
      }
    } catch (err) {
      console.error("Initial load error:", err);
    }
  };

  const loadCourseData = async (courseId: string) => {
    setLoading(true);
    try {
      const [m, recs, srcList, kMap, rev] = await Promise.allSettled([
        api.getMastery(courseId),
        api.getRecommendations(courseId),
        api.getSources(courseId),
        api.getKnowledgeMap(courseId),
        api.getRevisionPlan(courseId),
      ]);

      if (m.status === "fulfilled") setMasteryData(m.value);
      if (recs.status === "fulfilled") setRecommendations(recs.value);
      if (srcList.status === "fulfilled") setSources(srcList.value);
      if (kMap.status === "fulfilled") setKnowledgeMap(kMap.value);
      if (rev.status === "fulfilled") setRevisionPlan(rev.value);
    } catch (e) {
      console.error("Course data load error:", e);
    } finally {
      setLoading(false);
    }
  };

  // Tutor submission
  const handleSendTutor = async (queryText?: string) => {
    const q = queryText || tutorQuery;
    if (!q.trim()) return;

    const newMessages = [...chatMessages, { role: "user" as const, content: q }];
    setChatMessages(newMessages);
    setTutorQuery("");
    setTutorLoading(true);

    try {
      const res = await api.sendTutorChat({
        course_id: selectedCourseId,
        message: q,
        depth: tutorDepth,
        allow_outside_knowledge: allowOutsideKnowledge,
      });

      setChatMessages([
        ...newMessages,
        {
          role: "assistant",
          content: res.content,
          citations: res.citations,
          is_grounded: res.is_grounded,
          refused: res.refused,
          outside_knowledge_used: res.outside_knowledge_used,
        },
      ]);
    } catch (err: any) {
      setChatMessages([
        ...newMessages,
        {
          role: "assistant",
          content: `Error contacting EduNexus tutor service: ${err.message}`,
        },
      ]);
    } finally {
      setTutorLoading(false);
    }
  };

  // Assessment generation & submission
  const handleGenerateQuiz = async (topic?: string) => {
    setLoading(true);
    setAssessmentResult(null);
    setUserAnswers({});
    try {
      const asmt = await api.generateAssessment({
        course_id: selectedCourseId,
        topic: topic || selectedTopicForQuiz || undefined,
        mode: "practice",
        num_questions: 4,
      });
      setCurrentAssessment(asmt);
      setActiveTab("assessment");
    } catch (err: any) {
      alert(`Could not generate quiz: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitQuiz = async () => {
    if (!currentAssessment) return;
    setQuizSubmitting(true);
    try {
      const answersList = Object.entries(userAnswers).map(([qid, ans]) => ({
        question_id: qid,
        answer: ans,
      }));

      const res = await api.submitAssessment(currentAssessment.id, {
        student_id: "default_student",
        time_spent_secs: 60,
        answers: answersList,
      });

      setAssessmentResult(res);
      // Reload mastery to show live BKT progression
      api.getMastery(selectedCourseId).then(setMasteryData);
    } catch (err: any) {
      alert(`Failed to submit assessment: ${err.message}`);
    } finally {
      setQuizSubmitting(false);
    }
  };

  // Evaluation Runner
  const handleRunEvaluation = async () => {
    setEvalLoading(true);
    try {
      const data = await api.runEvaluation(selectedCourseId);
      setEvalRunData(data);
    } catch (err: any) {
      alert(`Evaluation failed: ${err.message}`);
    } finally {
      setEvalLoading(false);
    }
  };

  // Inspect Source Chunks
  const handleInspectSource = async (sourceId: string) => {
    setSelectedSourceForChunks(sourceId);
    try {
      const chunks = await api.getSourceChunks(sourceId);
      setInspectChunks(chunks);
    } catch (err) {
      console.error(err);
    }
  };

  // File Upload
  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploadProgress(true);
    try {
      const newSrc = await api.uploadSource(selectedCourseId, selectedFile);
      setStatusMessage(`Successfully uploaded and indexed "${newSrc.filename}"!`);
      setSelectedFile(null);
      // Refresh sources & mastery
      loadCourseData(selectedCourseId);
    } catch (err: any) {
      alert(`Upload error: ${err.message}`);
    } finally {
      setUploadProgress(false);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#090d16] text-slate-100 font-sans">
      {/* LEFT NAVIGATION SIDEBAR */}
      <aside className="w-64 border-r border-slate-800 bg-slate-950/70 flex flex-col justify-between shrink-0">
        <div>
          {/* Logo Brand */}
          <div className="p-5 border-b border-slate-800/80 flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-1.5">
                EduNexus <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 font-semibold border border-indigo-500/30">AI</span>
              </h1>
              <p className="text-[11px] text-slate-400 font-medium">Verified Adaptive Tutor</p>
            </div>
          </div>

          {/* Course Selector */}
          <div className="p-4 border-b border-slate-800/60">
            <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">
              Active Course
            </label>
            <select
              value={selectedCourseId}
              onChange={(e) => setSelectedCourseId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-2 text-xs font-medium text-slate-200 focus:outline-none focus:border-indigo-500 transition"
            >
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.code}: {c.title.length > 22 ? c.title.substring(0, 22) + "..." : c.title}
                </option>
              ))}
            </select>
          </div>

          {/* Nav Links */}
          <nav className="p-3 space-y-1">
            {[
              { id: "dashboard", label: "Student Dashboard", icon: BarChart3 },
              { id: "tutor", label: "Grounded AI Tutor", icon: BrainCircuit, badge: "Citations" },
              { id: "assessment", label: "Adaptive Quizzes", icon: GraduationCap },
              { id: "library", label: "Knowledge Library", icon: BookOpen },
              { id: "upload", label: "Multimodal Ingest", icon: UploadCloud },
              { id: "mastery", label: "Mastery Analytics (BKT)", icon: TrendingUp },
              { id: "revision", label: "Revision Studio", icon: Layers },
              { id: "evaluation", label: "RAG & Benchmark", icon: Award, badge: "Verified" },
              { id: "settings", label: "Settings & Status", icon: Sliders },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as NavTab)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition ${
                    isActive
                      ? "bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 font-semibold"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? "text-indigo-400" : "text-slate-400"}`} />
                    <span>{tab.label}</span>
                  </div>
                  {tab.badge && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* User profile / demo footer */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/40">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-indigo-300">
              ST
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-slate-200 truncate">Demo Student</p>
              <p className="text-[10px] text-emerald-400 flex items-center gap-1 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Offline/Demo Mode Active
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* MAIN VIEWPORT */}
      <main className="flex-1 flex flex-col overflow-hidden bg-gradient-to-b from-[#090d16] via-[#0d1322] to-[#090d16]">
        {/* TOP STATUS BAR */}
        <header className="h-14 border-b border-slate-800/70 px-6 flex items-center justify-between shrink-0 bg-slate-950/40 backdrop-blur-md">
          <div className="flex items-center space-x-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Course:</span>
            <span className="text-sm font-semibold text-white">
              {courses.find((c) => c.id === selectedCourseId)?.title || "Loading Course..."}
            </span>
          </div>

          <div className="flex items-center space-x-4">
            {masteryData && (
              <div className="flex items-center space-x-2 text-xs bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
                <span className="text-slate-400">Topic Mastery:</span>
                <span className="font-bold text-indigo-400">{Math.round(masteryData.overall_mastery * 100)}%</span>
                <span className="text-slate-600">|</span>
                <span className="text-slate-400">Streak:</span>
                <span className="font-bold text-amber-400">{masteryData.recent_streak_days} Days</span>
              </div>
            )}
            <button
              onClick={() => loadCourseData(selectedCourseId)}
              title="Refresh course data"
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </header>

        {/* CONTENT VIEW AREA */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* TAB 1: STUDENT DASHBOARD */}
          {activeTab === "dashboard" && masteryData && (
            <div className="space-y-6 animate-in fade-in duration-300">
              {/* Hero Banner */}
              <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-950/40 via-slate-900/60 to-purple-950/30 border border-indigo-500/20 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    Personalized Tutoring & Adaptive Progress
                  </h2>
                  <p className="text-xs text-slate-400 mt-1 max-w-xl">
                    EduNexus AI tracks your topic mastery through Bayesian Knowledge Tracing. All questions, tutor responses, and flashcards are strictly grounded in your indexed textbooks and slides.
                  </p>
                </div>
                <div className="flex items-center space-x-3 shrink-0">
                  <button
                    onClick={() => setActiveTab("tutor")}
                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition flex items-center gap-1.5"
                  >
                    <BrainCircuit className="w-3.5 h-3.5" /> Ask Tutor
                  </button>
                  <button
                    onClick={() => handleGenerateQuiz()}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition flex items-center gap-1.5"
                  >
                    <GraduationCap className="w-3.5 h-3.5" /> Take Adaptive Quiz
                  </button>
                </div>
              </div>

              {/* Analytics Metric Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-xs text-slate-400 block mb-1">Estimated Mastery (BKT)</span>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-2xl font-extrabold text-white">
                      {Math.round(masteryData.overall_mastery * 100)}%
                    </span>
                    <span className="text-xs font-medium text-emerald-400">Bayesian Posterior</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
                    <div
                      className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                      style={{ width: `${masteryData.overall_mastery * 100}%` }}
                    ></div>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-xs text-slate-400 block mb-1">Assessment Accuracy</span>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-2xl font-extrabold text-emerald-400">
                      {Math.round(masteryData.average_accuracy * 100)}%
                    </span>
                    <span className="text-xs text-slate-400">Across {masteryData.total_attempts} attempts</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-2">Verified scoring without guesswork</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-xs text-slate-400 block mb-1">Indexed Sources</span>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-2xl font-extrabold text-white">{sources.length}</span>
                    <span className="text-xs text-indigo-400">Textbooks & Slides</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-2">Exact page/slide citation anchors</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-xs text-slate-400 block mb-1">Topics Needing Review</span>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-2xl font-extrabold text-amber-400">{masteryData.weakest_topics.length}</span>
                    <span className="text-xs text-amber-300/80">Priority Targets</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-2">
                    {masteryData.weakest_topics.join(", ") || "All concepts strong!"}
                  </p>
                </div>
              </div>

              {/* Topic Mastery Distribution Chart */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
                  <h3 className="text-sm font-bold text-white mb-4 flex items-center justify-between">
                    <span>Topic-Wise Bayesian Knowledge Mastery</span>
                    <span className="text-xs font-normal text-slate-400">Probability of Knowledge P(L)</span>
                  </h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={masteryData.topics}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="topic" stroke="#64748b" fontSize={11} tickLine={false} />
                        <YAxis stroke="#64748b" fontSize={11} domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
                        <Tooltip
                          contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px" }}
                          formatter={(v: any) => [`${Math.round(v * 100)}% Mastery`, "Probability P(L)"]}
                        />
                        <Bar dataKey="p_l" fill="#6366f1" radius={[6, 6, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Targeted Recommendations List */}
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-1.5">
                      <Zap className="w-4 h-4 text-amber-400" /> Targeted Recommendations
                    </h3>
                    <p className="text-xs text-slate-400 mb-4">
                      Ordered by prerequisite dependencies and knowledge gaps.
                    </p>

                    <div className="space-y-2.5">
                      {recommendations.slice(0, 3).map((rec) => (
                        <div
                          key={rec.id}
                          className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-semibold text-slate-200">{rec.topic}</span>
                            <span
                              className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                                rec.priority === "high"
                                  ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                                  : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                              }`}
                            >
                              {rec.priority.toUpperCase()} PRIORITY
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400">{rec.reason}</p>
                          <button
                            onClick={() => handleGenerateQuiz(rec.topic)}
                            className="text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 mt-2 flex items-center gap-1"
                          >
                            Practice Quiz <ChevronRight className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={() => setActiveTab("revision")}
                    className="w-full mt-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 rounded-xl transition"
                  >
                    Open Revision Studio
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: SOURCE-GROUNDED AI TUTOR */}
          {activeTab === "tutor" && (
            <div className="flex flex-col h-[calc(100vh-120px)] space-y-4">
              {/* Tutor Header Controls */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center justify-between gap-3 shrink-0">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-semibold text-slate-400">Explanation Depth:</span>
                  {(["beginner", "intermediate", "advanced", "exam"] as const).map((d) => (
                    <button
                      key={d}
                      onClick={() => setTutorDepth(d)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium capitalize transition ${
                        tutorDepth === d
                          ? "bg-indigo-600 text-white font-semibold"
                          : "bg-slate-800 text-slate-400 hover:text-white"
                      }`}
                    >
                      {d}
                    </button>
                  ))}
                </div>

                <div className="flex items-center space-x-3">
                  <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={allowOutsideKnowledge}
                      onChange={(e) => setAllowOutsideKnowledge(e.target.checked)}
                      className="rounded border-slate-700 text-indigo-600 focus:ring-0"
                    />
                    <span>Allow Outside Knowledge</span>
                  </label>
                  {!allowOutsideKnowledge && (
                    <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                      Strict Grounding Active
                    </span>
                  )}
                </div>
              </div>

              {/* Chat Message History */}
              <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                {chatMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-2xl rounded-2xl p-4 text-xs leading-relaxed ${
                        msg.role === "user"
                          ? "bg-indigo-600 text-white rounded-br-none shadow-md"
                          : "bg-slate-900/80 border border-slate-800 text-slate-200 rounded-bl-none shadow-md"
                      }`}
                    >
                      {/* Refusal Warning Banner */}
                      {msg.refused && (
                        <div className="mb-3 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 flex items-center gap-2">
                          <ShieldAlert className="w-4 h-4 shrink-0" />
                          <span className="text-[11px] font-semibold">
                            Strict Abstention: Query outside active course documents.
                          </span>
                        </div>
                      )}

                      {/* Outside knowledge indicator */}
                      {msg.outside_knowledge_used && (
                        <div className="mb-3 p-2 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-300 text-[11px]">
                          <strong>[Outside Course Material]:</strong> This explanation draws from general AI knowledge, not course textbooks.
                        </div>
                      )}

                      {/* Message Content */}
                      <div className="whitespace-pre-wrap">{msg.content}</div>

                      {/* Verified Citations List */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-slate-800 space-y-2">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                            Verifiable Course Citations:
                          </span>
                          <div className="flex flex-wrap gap-2">
                            {msg.citations.map((cit, cIdx) => (
                              <button
                                key={cIdx}
                                onClick={() => setActiveCitation(cit)}
                                className="px-2.5 py-1 rounded-lg bg-indigo-950/40 border border-indigo-500/30 hover:border-indigo-400 text-indigo-300 text-[11px] flex items-center gap-1.5 transition"
                              >
                                {cit.source_type === "pptx" ? (
                                  <Presentation className="w-3 h-3 text-amber-400" />
                                ) : (
                                  <FileText className="w-3 h-3 text-indigo-400" />
                                )}
                                <span>
                                  {cit.page_number
                                    ? `Page ${cit.page_number}`
                                    : cit.slide_number
                                    ? `Slide ${cit.slide_number}`
                                    : "Citation"}
                                </span>
                                <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {tutorLoading && (
                  <div className="flex justify-start">
                    <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400 flex items-center space-x-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
                      <span>Retrieving course chunks and generating grounded explanation...</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Fast Example Prompts */}
              <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-800/60 shrink-0">
                <span className="text-[11px] text-slate-400 self-center font-medium">Try Sample:</span>
                {[
                  "What is the worst-case time complexity of QuickSort?",
                  "How many comparisons does Binary Search need for 1024 elements?",
                  "What is the secret recipe for baking artisanal French sourdough bread?",
                ].map((sample, sIdx) => (
                  <button
                    key={sIdx}
                    onClick={() => handleSendTutor(sample)}
                    className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition"
                  >
                    "{sample.substring(0, 36)}..."
                  </button>
                ))}
              </div>

              {/* Input Box */}
              <div className="flex items-center space-x-2 shrink-0">
                <input
                  type="text"
                  value={tutorQuery}
                  onChange={(e) => setTutorQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSendTutor()}
                  placeholder="Ask a question grounded in your course materials..."
                  className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
                <button
                  onClick={() => handleSendTutor()}
                  disabled={tutorLoading || !tutorQuery.trim()}
                  className="px-4 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition"
                >
                  <Send className="w-4 h-4" /> Send
                </button>
              </div>
            </div>
          )}

          {/* TAB 3: ADAPTIVE ASSESSMENT WORKSPACE */}
          {activeTab === "assessment" && (
            <div className="space-y-6">
              {!currentAssessment && !assessmentResult && (
                <div className="max-w-xl mx-auto p-8 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-4">
                  <div className="w-12 h-12 mx-auto rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                    <GraduationCap className="w-6 h-6" />
                  </div>
                  <h3 className="text-base font-bold text-white">Adaptive Diagnostic & Practice Engine</h3>
                  <p className="text-xs text-slate-400">
                    Questions are dynamically selected to match your Zone of Proximal Development (ZPD) based on your current Bayesian Knowledge Tracing topic mastery.
                  </p>
                  <div className="flex justify-center gap-3 pt-2">
                    <button
                      onClick={() => handleGenerateQuiz()}
                      className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/30 transition flex items-center gap-2"
                    >
                      <Play className="w-3.5 h-3.5" /> Start Adaptive Quiz
                    </button>
                  </div>
                </div>
              )}

              {/* Active Quiz Player */}
              {currentAssessment && !assessmentResult && (
                <div className="max-w-2xl mx-auto space-y-6">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <div>
                      <h3 className="text-base font-bold text-white">{currentAssessment.title}</h3>
                      <p className="text-xs text-slate-400">{currentAssessment.total_questions} Questions • Adaptive Practice Mode</p>
                    </div>
                    <div className="flex items-center space-x-1.5 text-xs text-amber-400 font-semibold bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-lg">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{currentAssessment.time_limit_mins}:00</span>
                    </div>
                  </div>

                  {/* Question Cards */}
                  <div className="space-y-6">
                    {currentAssessment.questions.map((q, idx) => (
                      <div key={q.id} className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-indigo-400">Question {idx + 1} of {currentAssessment.total_questions}</span>
                          <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-400 uppercase">
                            {q.difficulty}
                          </span>
                        </div>
                        <h4 className="text-sm font-semibold text-slate-100">{q.question_text}</h4>

                        {/* MCQ options */}
                        {q.options && q.options.length > 0 && (
                          <div className="space-y-2">
                            {q.options.map((opt, oIdx) => (
                              <label
                                key={oIdx}
                                className={`flex items-center p-3 rounded-xl border text-xs cursor-pointer transition ${
                                  userAnswers[q.id] === opt
                                    ? "bg-indigo-600/15 border-indigo-500 text-indigo-200"
                                    : "bg-slate-950/40 border-slate-800 text-slate-300 hover:bg-slate-800/40"
                                }`}
                              >
                                <input
                                  type="radio"
                                  name={`q_${q.id}`}
                                  value={opt}
                                  checked={userAnswers[q.id] === opt}
                                  onChange={() => setUserAnswers({ ...userAnswers, [q.id]: opt })}
                                  className="text-indigo-600 focus:ring-0 mr-3"
                                />
                                <span>{opt}</span>
                              </label>
                            ))}
                          </div>
                        )}

                        {/* Numerical or Short Answer input */}
                        {(!q.options || q.options.length === 0) && (
                          <div>
                            <input
                              type="text"
                              value={userAnswers[q.id] || ""}
                              onChange={(e) => setUserAnswers({ ...userAnswers, [q.id]: e.target.value })}
                              placeholder={q.question_type === "numerical" ? "Enter computed number (e.g. 10)" : "Type your answer..."}
                              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                            />
                            {q.question_type === "numerical" && (
                              <span className="text-[10px] text-slate-400 mt-1 block">
                                Re-evaluated deterministically against programmatically verified solution.
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  <div className="flex justify-end gap-3 pt-4">
                    <button
                      onClick={() => setCurrentAssessment(null)}
                      className="px-4 py-2 bg-slate-800 text-slate-400 hover:text-white text-xs font-semibold rounded-xl transition"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSubmitQuiz}
                      disabled={quizSubmitting || Object.keys(userAnswers).length === 0}
                      className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-lg shadow-indigo-600/30 transition flex items-center gap-1.5"
                    >
                      {quizSubmitting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                      Submit Quiz
                    </button>
                  </div>
                </div>
              )}

              {/* Assessment Results & Misconception Report */}
              {assessmentResult && (
                <div className="max-w-2xl mx-auto space-y-6">
                  <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-950/50 via-slate-900/60 to-emerald-950/30 border border-emerald-500/30 flex items-center justify-between">
                    <div>
                      <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">Assessment Completed</span>
                      <h3 className="text-2xl font-black text-white mt-1">
                        Score: {assessmentResult.score} / {assessmentResult.total_points} ({Math.round(assessmentResult.accuracy * 100)}%)
                      </h3>
                      <p className="text-xs text-slate-400 mt-1">
                        Next Action: {assessmentResult.recommended_next_action}
                      </p>
                    </div>
                    <button
                      onClick={() => handleGenerateQuiz()}
                      className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-xl border border-slate-700 transition"
                    >
                      Take Next Quiz
                    </button>
                  </div>

                  {/* BKT Mastery Shifts */}
                  <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                      Bayesian Knowledge Tracing (BKT) Posterior Updates
                    </h4>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      {Object.entries(assessmentResult.mastery_deltas).map(([top, delta]) => (
                        <div key={top} className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl">
                          <span className="font-semibold text-slate-200 block">{top}</span>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className="text-slate-400">{Math.round(delta.prior * 100)}%</span>
                            <span className="text-slate-500">→</span>
                            <span className="font-bold text-white">{Math.round(delta.posterior * 100)}%</span>
                            <span
                              className={`text-[10px] font-bold ${
                                delta.delta >= 0 ? "text-emerald-400" : "text-rose-400"
                              }`}
                            >
                              ({delta.delta >= 0 ? `+${Math.round(delta.delta * 100)}%` : `${Math.round(delta.delta * 100)}%`})
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Question Results Breakdown */}
                  <div className="space-y-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Detailed Feedback & Citations</h4>
                    {assessmentResult.question_results.map((qr, idx) => (
                      <div
                        key={idx}
                        className={`p-5 rounded-2xl border text-xs space-y-3 ${
                          qr.is_correct
                            ? "bg-emerald-950/10 border-emerald-500/20"
                            : "bg-rose-950/10 border-rose-500/20"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-200">Question {idx + 1}: {qr.question_text}</span>
                          <span
                            className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                              qr.is_correct ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400"
                            }`}
                          >
                            {qr.is_correct ? "CORRECT (+1.0)" : "INCORRECT (0.0)"}
                          </span>
                        </div>

                        <div className="space-y-1 text-[11px]">
                          <p>
                            <span className="text-slate-400">Your Answer:</span>{" "}
                            <span className={qr.is_correct ? "text-emerald-300 font-semibold" : "text-rose-300 font-semibold"}>
                              {qr.user_answer || "(None)"}
                            </span>
                          </p>
                          {!qr.is_correct && (
                            <p>
                              <span className="text-slate-400">Verified Solution:</span>{" "}
                              <span className="text-slate-200 font-semibold">{qr.correct_answer}</span>
                            </p>
                          )}
                          <p className="text-slate-300 mt-2">{qr.explanation}</p>
                        </div>

                        {/* Misconception Diagnostic */}
                        {qr.misconception && (
                          <div className="p-3 bg-slate-950/60 border border-rose-500/20 rounded-xl text-[11px] text-rose-200">
                            <strong>Diagnosed Misconception:</strong> {qr.misconception}
                          </div>
                        )}

                        {/* Verified Citations */}
                        {qr.citations && qr.citations.length > 0 && (
                          <div className="pt-2 flex items-center gap-2">
                            <span className="text-[10px] text-slate-400">Supporting Source:</span>
                            <button
                              onClick={() => setActiveCitation(qr.citations[0])}
                              className="text-[10px] text-indigo-400 underline font-medium hover:text-indigo-300"
                            >
                              {qr.citations[0].source_name} ({qr.citations[0].page_number ? `Page ${qr.citations[0].page_number}` : `Slide ${qr.citations[0].slide_number}`})
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: KNOWLEDGE & SOURCE LIBRARY */}
          {activeTab === "library" && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-white">Course Knowledge & Document Library</h3>
                  <p className="text-xs text-slate-400">
                    Extracted materials with preserved page numbers, slide boundaries, and concept tags.
                  </p>
                </div>
                <button
                  onClick={() => setActiveTab("upload")}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl flex items-center gap-1.5 transition"
                >
                  <UploadCloud className="w-3.5 h-3.5" /> Upload Material
                </button>
              </div>

              {/* Source Document Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {sources.map((src) => (
                  <div key={src.id} className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                        {src.source_type === "pptx" ? <Presentation className="w-5 h-5" /> : <FileText className="w-5 h-5" />}
                      </div>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
                        {src.status}
                      </span>
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-100 truncate">{src.filename}</h4>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        {src.page_count ? `${src.page_count} Pages` : src.slide_count ? `${src.slide_count} Slides` : "Notes"} • {src.chunk_count} Chunks
                      </p>
                    </div>

                    <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
                      <span className="text-slate-400">Method: {src.extraction_method}</span>
                      <button
                        onClick={() => handleInspectSource(src.id)}
                        className="text-indigo-400 hover:text-indigo-300 font-semibold"
                      >
                        Inspect Chunks →
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Visual Knowledge & Prerequisite Graph */}
              {knowledgeMap && (
                <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-white flex items-center gap-2">
                        <BrainCircuit className="w-4 h-4 text-indigo-400" /> Prerequisite Concept Map
                      </h4>
                      <p className="text-xs text-slate-400">
                        Directed Acyclic Graph (DAG) of foundational to advanced topics.
                      </p>
                    </div>
                    <span className="text-xs text-slate-400">{knowledgeMap.nodes.length} Nodes • {knowledgeMap.edges.length} Directed Edges</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                    {knowledgeMap.nodes.map((n) => (
                      <div key={n.id} className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-slate-200">{n.name}</span>
                          <span className="text-[10px] uppercase font-bold text-indigo-400">{n.difficulty}</span>
                        </div>
                        <p className="text-[11px] text-slate-400">{n.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Chunk Inspector Drawer / Modal */}
              {selectedSourceForChunks && (
                <div className="p-6 rounded-2xl bg-slate-900/80 border border-indigo-500/30 space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-white">
                      Extracted Chunks & Provenance Inspector ({inspectChunks.length} chunks)
                    </h4>
                    <button
                      onClick={() => setSelectedSourceForChunks(null)}
                      className="text-xs text-slate-400 hover:text-white"
                    >
                      Close Inspector ✕
                    </button>
                  </div>
                  <div className="max-h-80 overflow-y-auto space-y-3 pr-2">
                    {inspectChunks.map((c) => (
                      <div key={c.chunk_id} className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-2">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="font-mono text-indigo-300 font-semibold">{c.chunk_id}</span>
                          <span className="text-slate-400">
                            {c.page_number ? `Page ${c.page_number}` : c.slide_number ? `Slide ${c.slide_number}` : "Section"}
                          </span>
                        </div>
                        <p className="text-slate-300 leading-relaxed">{c.content}</p>
                        {c.concept_tags && c.concept_tags.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {c.concept_tags.map((t, idx) => (
                              <span key={idx} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                                #{t}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 5: MULTIMODAL INGESTION HUB */}
          {activeTab === "upload" && (
            <div className="max-w-xl mx-auto space-y-6">
              <div>
                <h3 className="text-base font-bold text-white">Multimodal Course Ingestion Hub</h3>
                <p className="text-xs text-slate-400">
                  Upload textbooks (PDF), lecture slide decks (PPTX), or notes (TXT/MD). Exact page numbers, slide boundaries, and headings are extracted automatically.
                </p>
              </div>

              {statusMessage && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{statusMessage}</span>
                </div>
              )}

              <form onSubmit={handleFileUpload} className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                <div className="border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-2xl p-8 text-center transition cursor-pointer">
                  <UploadCloud className="w-10 h-10 mx-auto text-indigo-400 mb-2" />
                  <p className="text-xs font-semibold text-slate-200">Drag and drop file here, or click to browse</p>
                  <p className="text-[11px] text-slate-400 mt-1">PDF, PPTX, TXT, MD, MP3, MP4 (Max 50MB)</p>
                  <input
                    type="file"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="mt-4 text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
                  />
                </div>

                {selectedFile && (
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs flex items-center justify-between">
                    <span className="font-semibold text-white truncate max-w-xs">{selectedFile.name}</span>
                    <span className="text-slate-400 font-mono">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={uploadProgress || !selectedFile}
                  className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl transition flex items-center justify-center gap-2"
                >
                  {uploadProgress ? <RefreshCw className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />}
                  <span>{uploadProgress ? "Ingesting & Preserving Provenance..." : "Process & Index File"}</span>
                </button>
              </form>

              <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/80 space-y-2 text-xs text-slate-400">
                <span className="font-bold text-slate-300 block">Multimodal Guarantee:</span>
                <p>• Scanned PDF pages automatically trigger OCR detection.</p>
                <p>• PPTX files preserve slide numbers and speaker notes.</p>
                <p>• Idempotent SHA256 hashing prevents duplicate re-indexing.</p>
              </div>
            </div>
          )}

          {/* TAB 6: LEARNER MASTERY (BKT) ANALYTICS */}
          {activeTab === "mastery" && masteryData && (
            <div className="space-y-6">
              <div>
                <h3 className="text-base font-bold text-white">Bayesian Knowledge Tracing (BKT) Learner Model</h3>
                <p className="text-xs text-slate-400">
                  Continuous mathematical estimation of skill mastery. Updates posterior probabilities on correct answers and slips, while applying Ebbinghaus forgetting curves.
                </p>
              </div>

              {/* Mathematical Formulation Explainer */}
              <div className="p-5 rounded-2xl bg-indigo-950/20 border border-indigo-500/30 text-xs space-y-2">
                <span className="font-bold text-indigo-200 block">BKT Mathematical Engine:</span>
                <p className="text-indigo-300 leading-relaxed font-mono text-[11px]">
                  P(L_t | Correct) = [P(L_t) * (1 - P(S))] / [P(L_t) * (1 - P(S)) + (1 - P(L_t)) * P(G)]
                </p>
                <p className="text-indigo-300 leading-relaxed font-mono text-[11px]">
                  P(L_{"{t+1}"}) = Posterior + (1 - Posterior) * P(T)
                </p>
                <p className="text-slate-400 text-[11px]">
                  Hyperparameters: Initial Mastery P(L0) = 0.20 | Transition P(T) = 0.15 | Guess P(G) = 0.25 | Slip P(S) = 0.10
                </p>
              </div>

              {/* Topic Mastery Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {masteryData.topics.map((t) => (
                  <div key={t.id} className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">{t.topic}</span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                          t.mastery_status === "mastered"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : t.mastery_status === "improving"
                            ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                            : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        }`}
                      >
                        {t.mastery_status.replace("_", " ")}
                      </span>
                    </div>

                    <div className="flex items-baseline space-x-2">
                      <span className="text-2xl font-black text-slate-100">{Math.round(t.p_l * 100)}%</span>
                      <span className="text-xs text-slate-400">± {Math.round(t.uncertainty * 100)}% unc.</span>
                    </div>

                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                        style={{ width: `${t.p_l * 100}%` }}
                      ></div>
                    </div>

                    <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                      <span>Attempts: {t.total_attempts}</span>
                      <span>Streak: {t.streak}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 7: REVISION STUDIO */}
          {activeTab === "revision" && revisionPlan && (
            <div className="space-y-6">
              <div>
                <h3 className="text-base font-bold text-white">Personalized Revision Studio</h3>
                <p className="text-xs text-slate-400">
                  Source-grounded flashcards, formula cheat sheets, and active recall summaries generated directly from indexed course documents.
                </p>
              </div>

              {/* Flashcards Grid */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400 mb-3">
                  Active Recall Flashcards (Click to flip)
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {revisionPlan.weak_topic_flashcards.map((fc, idx) => {
                    const isFlipped = !!flippedCards[idx];
                    return (
                      <div
                        key={idx}
                        onClick={() => setFlippedCards({ ...flippedCards, [idx]: !isFlipped })}
                        className={`h-48 p-5 rounded-2xl border cursor-pointer transition-all duration-300 flex flex-col justify-between ${
                          isFlipped
                            ? "bg-indigo-950/40 border-indigo-500/40 text-indigo-200"
                            : "bg-slate-900/60 border-slate-800 text-slate-200 hover:border-slate-700"
                        }`}
                      >
                        <div className="flex items-center justify-between text-[10px] uppercase font-bold text-slate-400">
                          <span>{fc.topic}</span>
                          <span>{isFlipped ? "Answer" : "Question (Click to flip)"}</span>
                        </div>
                        <p className="text-xs font-medium leading-relaxed my-auto">
                          {isFlipped ? fc.back : fc.front}
                        </p>
                        <span className="text-[10px] text-slate-500 truncate">Source: {fc.source_reference}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Formula Cheat Sheets */}
              {revisionPlan.formula_cheat_sheets.length > 0 && (
                <div className="pt-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400 mb-3">
                    High-Yield Formula Cheat Sheets
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {revisionPlan.formula_cheat_sheets.map((f, idx) => (
                      <div key={idx} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                        <span className="text-xs font-bold text-white block">{f.title}</span>
                        <p className="font-mono text-xs text-amber-300 bg-slate-950 p-2 rounded-lg border border-slate-800">
                          {f.formula}
                        </p>
                        <span className="text-[10px] text-slate-400 block pt-1">{f.source_reference}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 8: EVALUATION & BENCHMARK DASHBOARD */}
          {activeTab === "evaluation" && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-white">Evaluation & Benchmarking Engine</h3>
                  <p className="text-xs text-slate-400">
                    Live quantitative RAG benchmarks (faithfulness, relevancy, precision, recall, refusal accuracy) and simulated cohort learning experiments.
                  </p>
                </div>
                <button
                  onClick={handleRunEvaluation}
                  disabled={evalLoading}
                  className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-lg shadow-indigo-600/30 transition flex items-center gap-1.5"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${evalLoading ? "animate-spin" : ""}`} />
                  <span>{evalLoading ? "Running Benchmark Suite..." : "Run Live Benchmark Suite"}</span>
                </button>
              </div>

              {/* Benchmark Summary Metrics */}
              {evalRunData && (
                <div className="space-y-6 animate-in fade-in duration-300">
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                    {[
                      { label: "Faithfulness", value: `${Math.round(evalRunData.metrics.faithfulness * 100)}%`, color: "text-emerald-400" },
                      { label: "Answer Relevancy", value: `${Math.round(evalRunData.metrics.answer_relevancy * 100)}%`, color: "text-indigo-400" },
                      { label: "Context Precision", value: `${Math.round(evalRunData.metrics.context_precision * 100)}%`, color: "text-blue-400" },
                      { label: "Context Recall", value: `${Math.round(evalRunData.metrics.context_recall * 100)}%`, color: "text-purple-400" },
                      { label: "Citation Validity", value: `${Math.round(evalRunData.metrics.citation_validity_rate * 100)}%`, color: "text-emerald-400" },
                      { label: "Refusal Accuracy", value: `${Math.round(evalRunData.metrics.refusal_accuracy * 100)}%`, color: "text-amber-400" },
                    ].map((m, idx) => (
                      <div key={idx} className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
                        <span className="text-[10px] text-slate-400 block mb-1">{m.label}</span>
                        <span className={`text-xl font-black ${m.color}`}>{m.value}</span>
                      </div>
                    ))}
                  </div>

                  {/* Simulated Learner Cohorts: Adaptive vs Non-Adaptive Baseline */}
                  {evalRunData.simulated_cohort_results && (
                    <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                      <div>
                        <h4 className="text-sm font-bold text-white flex items-center gap-2">
                          <BrainCircuit className="w-4 h-4 text-indigo-400" /> Personalization Simulation Experiment
                        </h4>
                        <p className="text-xs text-slate-400">
                          Comparing Adaptive Question Selection against Random Baseline across simulated Beginner, Intermediate, and Advanced student cohorts.
                        </p>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {evalRunData.simulated_cohort_results.cohorts.map((c: any, idx: number) => (
                          <div key={idx} className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                            <span className="text-xs font-bold text-white block">{c.cohort_name} Cohort</span>
                            <div className="flex justify-between text-xs text-slate-400">
                              <span>Initial Mastery:</span>
                              <span className="font-semibold text-slate-200">{Math.round(c.initial_mastery * 100)}%</span>
                            </div>
                            <div className="flex justify-between text-xs text-indigo-300">
                              <span>Adaptive Final:</span>
                              <span className="font-bold text-indigo-400">{Math.round(c.final_mastery_adaptive * 100)}%</span>
                            </div>
                            <div className="flex justify-between text-xs text-slate-400">
                              <span>Random Baseline:</span>
                              <span className="font-semibold text-slate-300">{Math.round(c.final_mastery_random * 100)}%</span>
                            </div>
                            <div className="pt-2 border-t border-slate-800 flex justify-between text-xs">
                              <span className="text-emerald-400 font-semibold">Adaptive Gain:</span>
                              <span className="text-emerald-400 font-bold">+{c.adaptive_gain_percent}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Test Case Inspection Table */}
                  <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                    <h4 className="text-sm font-bold text-white">Granular Test Suite Results ({evalRunData.test_case_results.length} Cases)</h4>
                    <div className="max-h-64 overflow-y-auto pr-2">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-slate-800 text-slate-400">
                            <th className="pb-2">Test Case</th>
                            <th className="pb-2">Supported</th>
                            <th className="pb-2">Refusal</th>
                            <th className="pb-2">Faithfulness</th>
                            <th className="pb-2">Citation Validity</th>
                            <th className="pb-2">Latency</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {evalRunData.test_case_results.map((tc: any, idx: number) => (
                            <tr key={idx} className="hover:bg-slate-800/20">
                              <td className="py-2.5 font-medium text-slate-300 max-w-xs truncate">{tc.question}</td>
                              <td className="py-2.5">{tc.expected_supported ? "Yes" : "No (Negative)"}</td>
                              <td className="py-2.5">
                                <span className={tc.actual_refused ? "text-amber-400 font-semibold" : "text-slate-400"}>
                                  {tc.actual_refused ? "Refused" : "Answered"}
                                </span>
                              </td>
                              <td className="py-2.5 text-emerald-400 font-semibold">{Math.round(tc.faithfulness * 100)}%</td>
                              <td className="py-2.5 text-indigo-400 font-semibold">{Math.round(tc.citation_validity * 100)}%</td>
                              <td className="py-2.5 text-slate-400">{tc.latency_ms} ms</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 9: SETTINGS & SYSTEM STATUS */}
          {activeTab === "settings" && (
            <div className="max-w-xl mx-auto space-y-6">
              <div>
                <h3 className="text-base font-bold text-white">Settings & System Configuration</h3>
                <p className="text-xs text-slate-400">
                  Configure AI model providers, view database connection status, and verify deployment parameters.
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 text-xs">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <span className="font-semibold text-slate-200">LLM Provider Mode</span>
                  <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                    Local Deterministic & Offline Fallback Active
                  </span>
                </div>

                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <span className="font-semibold text-slate-200">Google Gemini API</span>
                  <span className="text-slate-400 font-medium">Configurable via GEMINI_API_KEY (.env)</span>
                </div>

                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <span className="font-semibold text-slate-200">Database Layer</span>
                  <span className="text-indigo-400 font-mono font-medium">SQLite (Local) / PostgreSQL Ready</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200">Embedding Engine</span>
                  <span className="text-slate-300 font-medium">Deterministic Dense Projection (128-dim)</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* VERIFIED CITATION MODAL */}
      <CitationModal citation={activeCitation} onClose={() => setActiveCitation(null)} />
    </div>
  );
}
