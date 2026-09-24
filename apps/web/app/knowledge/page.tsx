"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  BookOpen,
  Bot,
  BrainCircuit,
  Calendar,
  Check,
  ChevronRight,
  Clock,
  Compass,
  Copy,
  Database,
  ExternalLink,
  Eye,
  FileCode,
  FileText,
  Filter,
  HelpCircle,
  History,
  Layers,
  Lightbulb,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Tag,
  Trash2,
  User as UserIcon,
  X,
} from "lucide-react";
import {
  api,
  Company,
  KnowledgeCategory,
  KnowledgeConfidence,
  KnowledgeCreatePayload,
  KnowledgeItem,
  KnowledgeQueryCitation,
  KnowledgeQueryResponse,
  KnowledgeSourceType,
  KnowledgeUpdatePayload,
  Project,
  SelectiveContextResponse,
} from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

const CATEGORY_CONFIG: Record<
  string,
  { label: string; bg: string; text: string; border: string; icon: React.ComponentType<{ className?: string }> }
> = {
  STRATEGY: {
    label: "Strategy",
    bg: "bg-indigo-500/10",
    text: "text-indigo-400",
    border: "border-indigo-500/30",
    icon: Compass,
  },
  RESEARCH: {
    label: "Research",
    bg: "bg-cyan-500/10",
    text: "text-cyan-400",
    border: "border-cyan-500/30",
    icon: Lightbulb,
  },
  POLICY: {
    label: "Policy",
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/30",
    icon: ShieldCheck,
  },
  DECISION_RATIONALE: {
    label: "Decision Rationale",
    bg: "bg-purple-500/10",
    text: "text-purple-400",
    border: "border-purple-500/30",
    icon: BrainCircuit,
  },
  PROCEDURE: {
    label: "Procedure",
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/30",
    icon: FileCode,
  },
  HISTORICAL_RESULT: {
    label: "Historical Result",
    bg: "bg-rose-500/10",
    text: "text-rose-400",
    border: "border-rose-500/30",
    icon: History,
  },
  MEETING_NOTE: {
    label: "Meeting Note",
    bg: "bg-blue-500/10",
    text: "text-blue-400",
    border: "border-blue-500/30",
    icon: Calendar,
  },
  GENERAL: {
    label: "General Knowledge",
    bg: "bg-slate-500/10",
    text: "text-slate-300",
    border: "border-slate-500/30",
    icon: BookOpen,
  },
};

const CONFIDENCE_CONFIG: Record<string, { label: string; badge: string }> = {
  HIGH: { label: "High Confidence", badge: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" },
  MEDIUM: { label: "Medium Confidence", badge: "bg-amber-500/15 text-amber-300 border-amber-500/30" },
  LOW: { label: "Low Confidence", badge: "bg-rose-500/15 text-rose-300 border-rose-500/30" },
  ESTIMATED: { label: "Estimated", badge: "bg-purple-500/15 text-purple-300 border-purple-500/30" },
};

const CANONICAL_QUESTIONS = [
  "Why did we make this decision?",
  "What research supports it?",
  "What happened last time?",
  "Which projects depend on this decision?",
  "Which documents contain relevant information?",
];

export default function KnowledgePage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [knowledgeList, setKnowledgeList] = useState<KnowledgeItem[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedProjectId, setSelectedProjectId] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Inspection Drawer
  const [inspectedItem, setInspectedItem] = useState<KnowledgeItem | null>(null);

  // Q&A Inquiry State
  const [showInquiryCard, setShowInquiryCard] = useState<boolean>(true);
  const [inquiryQuestion, setInquiryQuestion] = useState<string>("");
  const [querying, setQuerying] = useState<boolean>(false);
  const [queryResponse, setQueryResponse] = useState<KnowledgeQueryResponse | null>(null);

  // Selective Context Synthesizer State
  const [showContextModal, setShowContextModal] = useState<boolean>(false);
  const [contextKeywords, setContextKeywords] = useState<string>("");
  const [contextProjectId, setContextProjectId] = useState<string>("");
  const [synthesizingContext, setSynthesizingContext] = useState<boolean>(false);
  const [selectiveContext, setSelectiveContext] = useState<SelectiveContextResponse | null>(null);
  const [copiedContext, setCopiedContext] = useState<boolean>(false);

  // Create / Edit Modal State
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [editingItem, setEditingItem] = useState<KnowledgeItem | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [formData, setFormData] = useState<{
    title: string;
    category: KnowledgeCategory;
    content: string;
    source_type: KnowledgeSourceType;
    source_uri: string;
    author_name: string;
    confidence: KnowledgeConfidence;
    project_id: string;
    tags: string;
    metadata_json: string;
  }>({
    title: "",
    category: "STRATEGY",
    content: "",
    source_type: "RESEARCH",
    source_uri: "",
    author_name: "",
    confidence: "HIGH",
    project_id: "",
    tags: "",
    metadata_json: "{}",
  });

  // Load Companies
  useEffect(() => {
    async function init() {
      try {
        const comps = await api.getCompanies();
        setCompanies(comps);
        if (comps.length > 0) {
          setSelectedCompanyId(comps[0].id);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load companies");
      }
    }
    init();
  }, []);

  // Load Projects for selected company
  useEffect(() => {
    if (!selectedCompanyId) return;
    async function loadProjects() {
      try {
        const projs = await api.getProjects(selectedCompanyId);
        setProjects(projs.items || []);
      } catch {
        setProjects([]);
      }
    }
    loadProjects();
  }, [selectedCompanyId]);

  // Load Knowledge Items
  const loadKnowledge = useCallback(async () => {
    if (!selectedCompanyId) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await api.getCompanyKnowledge(selectedCompanyId, {
        category: selectedCategory === "ALL" ? undefined : selectedCategory,
        project_id: selectedProjectId === "ALL" ? undefined : selectedProjectId,
        search: searchQuery.trim() || undefined,
        page: 1,
        page_size: 50,
      });
      setKnowledgeList(resp.items);
      setTotalCount(resp.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load company knowledge records");
    } finally {
      setLoading(false);
    }
  }, [selectedCompanyId, selectedCategory, selectedProjectId, searchQuery]);

  useEffect(() => {
    loadKnowledge();
  }, [loadKnowledge]);

  // Handle Q&A Inquiry
  const handleAskQuestion = async (qText?: string) => {
    const questionToAsk = (qText ?? inquiryQuestion).trim();
    if (!questionToAsk || !selectedCompanyId) return;

    setInquiryQuestion(questionToAsk);
    setQuerying(true);
    try {
      const resp = await api.queryCompanyKnowledge(
        selectedCompanyId,
        questionToAsk,
        selectedProjectId === "ALL" ? undefined : selectedProjectId
      );
      setQueryResponse(resp);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Knowledge inquiry failed");
    } finally {
      setQuerying(false);
    }
  };

  // Handle Selective Context Retrieval
  const handleSynthesizeContext = async () => {
    if (!selectedCompanyId) return;
    setSynthesizingContext(true);
    try {
      const keywords = contextKeywords
        .split(",")
        .map((k) => k.trim())
        .filter(Boolean);
      const resp = await api.getSelectiveContext(selectedCompanyId, {
        project_id: contextProjectId || undefined,
        intent_keywords: keywords,
        max_items: 10,
      });
      setSelectiveContext(resp);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Context synthesis failed");
    } finally {
      setSynthesizingContext(false);
    }
  };

  // Handle Create or Edit Submit
  const handleSaveKnowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCompanyId) return;
    setSubmitting(true);
    try {
      let metaObj = {};
      try {
        metaObj = JSON.parse(formData.metadata_json || "{}");
      } catch {
        metaObj = {};
      }

      const tagsList = formData.tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);

      if (editingItem) {
        const updatePayload: KnowledgeUpdatePayload = {
          title: formData.title,
          category: formData.category,
          content: formData.content,
          source_type: formData.source_type,
          source_uri: formData.source_uri || null,
          author_name: formData.author_name || null,
          confidence: formData.confidence,
          project_id: formData.project_id || null,
          tags: tagsList,
          metadata: metaObj,
        };
        const updated = await api.updateKnowledgeItem(selectedCompanyId, editingItem.id, updatePayload);
        setKnowledgeList((prev) => prev.map((k) => (k.id === updated.id ? updated : k)));
        if (inspectedItem?.id === updated.id) {
          setInspectedItem(updated);
        }
      } else {
        const createPayload: KnowledgeCreatePayload = {
          title: formData.title,
          category: formData.category,
          content: formData.content,
          source_type: formData.source_type,
          source_uri: formData.source_uri || null,
          author_name: formData.author_name || null,
          confidence: formData.confidence,
          project_id: formData.project_id || null,
          tags: tagsList,
          metadata: metaObj,
        };
        const created = await api.createKnowledgeItem(selectedCompanyId, createPayload);
        setKnowledgeList((prev) => [created, ...prev]);
        setTotalCount((c) => c + 1);
      }

      setShowCreateModal(false);
      setEditingItem(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save knowledge record");
    } finally {
      setSubmitting(false);
    }
  };

  // Handle Delete
  const handleDeleteKnowledge = async (itemId: string) => {
    if (!selectedCompanyId || !window.confirm("Are you sure you want to delete this company knowledge record?")) {
      return;
    }
    try {
      await api.deleteKnowledgeItem(selectedCompanyId, itemId);
      setKnowledgeList((prev) => prev.filter((k) => k.id !== itemId));
      setTotalCount((c) => Math.max(0, c - 1));
      if (inspectedItem?.id === itemId) {
        setInspectedItem(null);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete knowledge record");
    }
  };

  const openEditModal = (item: KnowledgeItem) => {
    setEditingItem(item);
    setFormData({
      title: item.title,
      category: (item.category as KnowledgeCategory) || "GENERAL",
      content: item.content,
      source_type: (item.source_type as KnowledgeSourceType) || "USER",
      source_uri: item.source_uri || "",
      author_name: item.author_name || "",
      confidence: (item.confidence as KnowledgeConfidence) || "HIGH",
      project_id: item.project_id || "",
      tags: (item.tags || []).join(", "),
      metadata_json: JSON.stringify(item.metadata || {}, null, 2),
    });
    setShowCreateModal(true);
  };

  const openCreateModal = () => {
    setEditingItem(null);
    setFormData({
      title: "",
      category: "STRATEGY",
      content: "",
      source_type: "RESEARCH",
      source_uri: "",
      author_name: "",
      confidence: "HIGH",
      project_id: selectedProjectId === "ALL" ? "" : selectedProjectId,
      tags: "",
      metadata_json: "{}",
    });
    setShowCreateModal(true);
  };

  // KPI Calculations
  const highConfCount = knowledgeList.filter((k) => k.confidence === "HIGH").length;
  const strategiesCount = knowledgeList.filter((k) =>
    ["STRATEGY", "POLICY", "DECISION_RATIONALE"].includes(k.category)
  ).length;
  const researchCount = knowledgeList.filter((k) =>
    ["RESEARCH", "HISTORICAL_RESULT", "PROCEDURE"].includes(k.category)
  ).length;

  return (
    <ShellLayout pageTitle="Company Knowledge" breadcrumb="Organization & Leadership">
      <div className="flex flex-col min-h-screen bg-[#080b11] text-slate-100 pb-16">
        {/* Top Header Bar */}
        <div className="border-b border-[#1e2738] bg-[#0c1017]/80 backdrop-blur-md sticky top-0 z-20 px-6 py-4">
          <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/25 flex items-center justify-center text-cyan-400 shadow-inner">
                <BookOpen className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold tracking-tight text-white">Company Knowledge Base</h1>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/25">
                    Phase 19 Active
                  </span>
                </div>
                <p className="text-xs text-slate-400">
                  Authoritative multi-tenant knowledge repository &amp; selective context retrieval for agents
                </p>
              </div>
            </div>

            {/* Action Bar */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Company Selector */}
              {companies.length > 1 && (
                <select
                  value={selectedCompanyId}
                  onChange={(e) => setSelectedCompanyId(e.target.value)}
                  className="bg-[#111724] border border-[#1e2738] text-xs text-slate-200 rounded-lg px-3 py-2 outline-none focus:border-cyan-500 transition"
                >
                  {companies.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              )}

              {/* Selective Context Trigger */}
              <button
                onClick={() => {
                  setShowContextModal(true);
                  if (!selectiveContext) handleSynthesizeContext();
                }}
                className="flex items-center gap-2 bg-[#111724] hover:bg-[#161f30] text-cyan-300 border border-cyan-500/30 text-xs font-semibold px-3 py-2 rounded-lg transition"
              >
                <BrainCircuit className="w-3.5 h-3.5 text-cyan-400" />
                <span>Selective Context</span>
              </button>

              {/* Create Knowledge Button */}
              <button
                onClick={openCreateModal}
                className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-semibold text-xs px-3.5 py-2 rounded-lg transition shadow-lg shadow-cyan-600/20"
              >
                <Plus className="w-4 h-4 text-slate-950" />
                <span>New Knowledge</span>
              </button>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="max-w-7xl mx-auto w-full px-6 py-6 space-y-6">
          {/* Error Banner */}
          {error && (
            <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-300 flex items-center justify-between text-xs animate-in fade-in">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                <span>{error}</span>
              </div>
              <button onClick={() => setError(null)} className="text-rose-400 hover:text-white transition">
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Executive KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl border border-[#1e2738] bg-[#0e1420] shadow-sm flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-slate-400">Total Knowledge Records</p>
                <h3 className="text-2xl font-bold text-white mt-1">{totalCount}</h3>
                <p className="text-[11px] text-cyan-400 mt-1 flex items-center gap-1 font-mono">
                  <Database className="w-3 h-3" /> Grounded &amp; Durable
                </p>
              </div>
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                <BookOpen className="w-5 h-5" />
              </div>
            </div>

            <div className="p-4 rounded-xl border border-[#1e2738] bg-[#0e1420] shadow-sm flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-slate-400">High Confidence Precedents</p>
                <h3 className="text-2xl font-bold text-emerald-400 mt-1">{highConfCount}</h3>
                <p className="text-[11px] text-slate-400 mt-1 font-mono">
                  {totalCount > 0 ? Math.round((highConfCount / totalCount) * 100) : 100}% verified
                </p>
              </div>
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
            </div>

            <div className="p-4 rounded-xl border border-[#1e2738] bg-[#0e1420] shadow-sm flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-slate-400">Strategies &amp; Policies</p>
                <h3 className="text-2xl font-bold text-indigo-400 mt-1">{strategiesCount}</h3>
                <p className="text-[11px] text-slate-400 mt-1 font-mono">Architectural Determinations</p>
              </div>
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                <Compass className="w-5 h-5" />
              </div>
            </div>

            <div className="p-4 rounded-xl border border-[#1e2738] bg-[#0e1420] shadow-sm flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-slate-400">Research &amp; Results</p>
                <h3 className="text-2xl font-bold text-purple-400 mt-1">{researchCount}</h3>
                <p className="text-[11px] text-slate-400 mt-1 font-mono">Empirical Learnings</p>
              </div>
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                <Lightbulb className="w-5 h-5" />
              </div>
            </div>
          </div>

          {/* Canonical Grounded Inquiries Card (Section 23 Core Questions) */}
          <div className="rounded-2xl border border-cyan-500/30 bg-[#0c1424] p-5 shadow-xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-80 h-80 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <h2 className="text-sm font-semibold text-white tracking-wide">
                  Ask Company Knowledge (Section 23 Canonical Inquiries)
                </h2>
              </div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/25">
                Grounding Engine
              </span>
            </div>

            {/* Prompt Chips */}
            <div className="flex flex-wrap gap-2 mb-3">
              {CANONICAL_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => handleAskQuestion(q)}
                  disabled={querying}
                  className="text-xs px-3 py-1.5 rounded-lg bg-[#111c30] hover:bg-cyan-500/20 text-cyan-200 border border-cyan-500/30 hover:border-cyan-400 transition flex items-center gap-1.5"
                >
                  <HelpCircle className="w-3 h-3 text-cyan-400" />
                  <span>{q}</span>
                </button>
              ))}
            </div>

            {/* Question Input */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAskQuestion();
              }}
              className="flex items-center gap-2"
            >
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Ask a question about decisions, research, past executions, or dependencies..."
                  value={inquiryQuestion}
                  onChange={(e) => setInquiryQuestion(e.target.value)}
                  className="w-full bg-[#0a0f1d] border border-[#1e2738] focus:border-cyan-500 pl-10 pr-4 py-2.5 rounded-xl text-xs text-white placeholder-slate-500 outline-none transition"
                />
              </div>
              <button
                type="submit"
                disabled={querying || !inquiryQuestion.trim()}
                className="bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-semibold px-4 py-2.5 rounded-xl text-xs flex items-center gap-2 transition"
              >
                {querying ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                <span>Ask</span>
              </button>
            </form>

            {/* Grounded Answer Panel */}
            {queryResponse && (
              <div className="mt-4 p-4 rounded-xl border border-[#1e2738] bg-[#090e1a] animate-in fade-in space-y-3">
                <div className="flex items-center justify-between border-b border-[#1e2738] pb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-cyan-400 font-semibold">
                      Q: {queryResponse.question}
                    </span>
                    {queryResponse.canonical_topic && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/25">
                        {queryResponse.canonical_topic}
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {new Date(queryResponse.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                <div className="text-xs text-slate-200 leading-relaxed whitespace-pre-line font-sans">
                  {queryResponse.answer}
                </div>

                {/* Grounded Citations */}
                {queryResponse.citations && queryResponse.citations.length > 0 && (
                  <div className="pt-2 border-t border-[#1e2738]">
                    <p className="text-[11px] font-semibold text-slate-400 mb-1.5 flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3 text-emerald-400" />
                      Grounded Provenance Citations ({queryResponse.citations.length}):
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {queryResponse.citations.map((c, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#131c2d] border border-[#1e2738] text-[11px] text-slate-300"
                        >
                          <span className="text-[9px] font-mono px-1 rounded bg-slate-800 text-cyan-400">
                            {c.source_type}
                          </span>
                          <span className="font-medium text-white">{c.title}</span>
                          <span className="text-slate-500 text-[10px] font-mono">[{c.confidence}]</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Filtering and Search Controls */}
          <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
            {/* Category Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-2 md:pb-0 scrollbar-none">
              <button
                onClick={() => setSelectedCategory("ALL")}
                className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition shrink-0 ${
                  selectedCategory === "ALL"
                    ? "bg-cyan-500/15 border-cyan-500/40 text-cyan-300 font-semibold"
                    : "bg-[#0e1420] border-[#1e2738] text-slate-400 hover:text-white"
                }`}
              >
                All Categories ({totalCount})
              </button>
              {Object.keys(CATEGORY_CONFIG).map((catKey) => {
                const conf = CATEGORY_CONFIG[catKey];
                const active = selectedCategory === catKey;
                return (
                  <button
                    key={catKey}
                    onClick={() => setSelectedCategory(catKey)}
                    className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition shrink-0 flex items-center gap-1.5 ${
                      active
                        ? `${conf.bg} ${conf.border} ${conf.text} font-semibold`
                        : "bg-[#0e1420] border-[#1e2738] text-slate-400 hover:text-white"
                    }`}
                  >
                    <span>{conf.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Filter by Project & Search Bar */}
            <div className="flex items-center gap-2">
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="bg-[#0e1420] border border-[#1e2738] text-xs text-slate-200 rounded-lg px-2.5 py-1.5 outline-none focus:border-cyan-500 transition"
              >
                <option value="ALL">All Projects</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>

              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter records..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-[#0e1420] border border-[#1e2738] focus:border-cyan-500 pl-8 pr-3 py-1.5 rounded-lg text-xs text-white placeholder-slate-500 outline-none transition w-44"
                />
              </div>

              <button
                onClick={loadKnowledge}
                title="Refresh knowledge list"
                className="p-2 rounded-lg bg-[#0e1420] border border-[#1e2738] hover:border-cyan-500/40 text-slate-400 hover:text-cyan-300 transition"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>

          {/* Knowledge Item Grid */}
          {loading && knowledgeList.length === 0 ? (
            <div className="p-16 flex flex-col items-center justify-center text-slate-400 space-y-3">
              <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
              <p className="text-xs">Loading persistent company knowledge...</p>
            </div>
          ) : knowledgeList.length === 0 ? (
            <div className="p-16 rounded-2xl border border-dashed border-[#1e2738] bg-[#0c1017] text-center space-y-3">
              <BookOpen className="w-8 h-8 text-slate-500 mx-auto" />
              <h3 className="text-sm font-semibold text-slate-300">No knowledge records found</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                No entries match your current filter. Record strategies, policies, research, and post-mortems for durable agent context.
              </p>
              <button
                onClick={openCreateModal}
                className="inline-flex items-center gap-1.5 text-xs text-cyan-400 bg-cyan-500/10 hover:bg-cyan-500/20 px-3 py-1.5 rounded-lg border border-cyan-500/30 transition"
              >
                <Plus className="w-3.5 h-3.5" /> Create First Knowledge Item
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {knowledgeList.map((item) => {
                const catConf = CATEGORY_CONFIG[item.category] || CATEGORY_CONFIG.GENERAL;
                const confBadge = CONFIDENCE_CONFIG[item.confidence] || CONFIDENCE_CONFIG.HIGH;
                const IconComponent = catConf.icon;

                return (
                  <div
                    key={item.id}
                    onClick={() => setInspectedItem(item)}
                    className="p-4 rounded-xl border border-[#1e2738] bg-[#0e1420] hover:border-cyan-500/40 hover:bg-[#111726] transition cursor-pointer flex flex-col justify-between group shadow-sm"
                  >
                    <div>
                      {/* Top Badges */}
                      <div className="flex items-center justify-between gap-2 mb-2.5">
                        <span
                          className={`text-[10px] font-medium px-2 py-0.5 rounded-full border flex items-center gap-1 ${catConf.bg} ${catConf.border} ${catConf.text}`}
                        >
                          <IconComponent className="w-3 h-3" />
                          {catConf.label}
                        </span>

                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${confBadge.badge}`}>
                          {item.confidence}
                        </span>
                      </div>

                      {/* Title */}
                      <h3 className="text-sm font-semibold text-white group-hover:text-cyan-300 transition line-clamp-2">
                        {item.title}
                      </h3>

                      {/* Content Preview */}
                      <p className="text-xs text-slate-400 mt-2 line-clamp-3 leading-relaxed">
                        {item.content}
                      </p>
                    </div>

                    {/* Metadata & Tags Footer */}
                    <div className="mt-4 pt-3 border-t border-[#1e2738]/60 space-y-2">
                      {item.tags && item.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {item.tags.slice(0, 3).map((tag, tIdx) => (
                            <span
                              key={tIdx}
                              className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700/60 font-mono"
                            >
                              #{tag}
                            </span>
                          ))}
                          {item.tags.length > 3 && (
                            <span className="text-[10px] text-slate-500 font-mono">
                              +{item.tags.length - 3}
                            </span>
                          )}
                        </div>
                      )}

                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span className="truncate max-w-[120px]">By {item.author_name}</span>
                        <span className="font-mono text-slate-400">
                          {new Date(item.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Detailed Inspection Drawer */}
        {inspectedItem && (
          <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-in fade-in">
            <div className="w-full max-w-xl bg-[#0c1017] border-l border-[#1e2738] h-full flex flex-col p-6 overflow-y-auto space-y-5 shadow-2xl">
              {/* Header */}
              <div className="flex items-center justify-between border-b border-[#1e2738] pb-4">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs px-2.5 py-1 rounded-full border ${
                      (CATEGORY_CONFIG[inspectedItem.category] || CATEGORY_CONFIG.GENERAL).bg
                    } ${(CATEGORY_CONFIG[inspectedItem.category] || CATEGORY_CONFIG.GENERAL).text} ${(CATEGORY_CONFIG[inspectedItem.category] || CATEGORY_CONFIG.GENERAL).border}`}
                  >
                    {inspectedItem.category}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">ID: {inspectedItem.id.slice(0, 8)}</span>
                </div>
                <button
                  onClick={() => setInspectedItem(null)}
                  className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Title & Author */}
              <div>
                <h2 className="text-lg font-bold text-white leading-snug">{inspectedItem.title}</h2>
                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-2">
                  <span className="flex items-center gap-1">
                    <UserIcon className="w-3.5 h-3.5 text-cyan-400" /> {inspectedItem.author_name}
                  </span>
                  <span className="flex items-center gap-1 font-mono text-slate-400">
                    <Clock className="w-3.5 h-3.5" /> {new Date(inspectedItem.created_at).toLocaleString()}
                  </span>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                      (CONFIDENCE_CONFIG[inspectedItem.confidence] || CONFIDENCE_CONFIG.HIGH).badge
                    }`}
                  >
                    {inspectedItem.confidence}
                  </span>
                </div>
              </div>

              {/* Provenance & Source */}
              <div className="p-3 rounded-lg border border-[#1e2738] bg-[#0e1420] text-xs space-y-1.5">
                <div className="flex items-center justify-between text-slate-400">
                  <span className="font-medium text-slate-300">Source Type:</span>
                  <span className="font-mono text-cyan-400">{inspectedItem.source_type}</span>
                </div>
                {inspectedItem.source_uri && (
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="font-medium text-slate-300">Source URI:</span>
                    <a
                      href={inspectedItem.source_uri}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-mono text-cyan-400 hover:underline flex items-center gap-1 truncate max-w-[260px]"
                    >
                      {inspectedItem.source_uri} <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                )}
                {inspectedItem.project_id && (
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="font-medium text-slate-300">Linked Project:</span>
                    <span className="font-mono text-slate-300">
                      {projects.find((p) => p.id === inspectedItem.project_id)?.name || inspectedItem.project_id}
                    </span>
                  </div>
                )}
                {inspectedItem.decision_id && (
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="font-medium text-slate-300">Linked Decision:</span>
                    <span className="font-mono text-purple-400">{inspectedItem.decision_id.slice(0, 8)}</span>
                  </div>
                )}
                {inspectedItem.artifact_id && (
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="font-medium text-slate-300">Linked Artifact:</span>
                    <span className="font-mono text-indigo-400">{inspectedItem.artifact_id.slice(0, 8)}</span>
                  </div>
                )}
              </div>

              {/* Full Content */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Content</h4>
                <div className="p-4 rounded-xl border border-[#1e2738] bg-[#090d15] text-xs text-slate-200 leading-relaxed font-sans whitespace-pre-wrap select-text">
                  {inspectedItem.content}
                </div>
              </div>

              {/* Tags */}
              {inspectedItem.tags && inspectedItem.tags.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Tags</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {inspectedItem.tags.map((t, idx) => (
                      <span
                        key={idx}
                        className="text-xs px-2 py-0.5 rounded-md bg-slate-800 text-cyan-300 border border-slate-700 font-mono"
                      >
                        #{t}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Metadata JSON */}
              {inspectedItem.metadata && Object.keys(inspectedItem.metadata).length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Metadata</h4>
                  <pre className="p-3 rounded-lg bg-[#090d15] border border-[#1e2738] text-[11px] text-slate-300 font-mono overflow-x-auto">
                    {JSON.stringify(inspectedItem.metadata, null, 2)}
                  </pre>
                </div>
              )}

              {/* Drawer Actions */}
              <div className="pt-4 border-t border-[#1e2738] flex items-center justify-between">
                <button
                  onClick={() => openEditModal(inspectedItem)}
                  className="px-3.5 py-2 rounded-lg bg-[#111724] hover:bg-[#182133] text-xs font-medium text-slate-200 border border-[#1e2738] transition"
                >
                  Edit Record
                </button>
                <button
                  onClick={() => handleDeleteKnowledge(inspectedItem.id)}
                  className="px-3.5 py-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-xs font-medium text-rose-300 border border-rose-500/30 transition flex items-center gap-1.5"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Delete Record</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Selective Context Synthesizer Modal (Section 23 Acceptance Criteria) */}
        {showContextModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
            <div className="bg-[#0c1017] border border-cyan-500/30 rounded-2xl max-w-2xl w-full p-6 space-y-4 shadow-2xl relative max-h-[90vh] flex flex-col">
              <div className="flex items-center justify-between border-b border-[#1e2738] pb-3">
                <div className="flex items-center gap-2">
                  <BrainCircuit className="w-5 h-5 text-cyan-400" />
                  <h3 className="text-sm font-bold text-white">
                    Agent Selective Context Synthesizer
                  </h3>
                </div>
                <button
                  onClick={() => setShowContextModal(false)}
                  className="text-slate-400 hover:text-white transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <p className="text-xs text-slate-400">
                Fulfills Section 23 Acceptance Criteria: <em>&quot;Agents can retrieve relevant historical company context without loading the entire database.&quot;</em>
              </p>

              {/* Context Parameters */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block text-slate-400 mb-1">Target Project</label>
                  <select
                    value={contextProjectId}
                    onChange={(e) => setContextProjectId(e.target.value)}
                    className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-cyan-500"
                  >
                    <option value="">Company-Wide Scope</option>
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Intent Keywords (comma-separated)</label>
                  <input
                    type="text"
                    placeholder="e.g. pgvector, indexing, latency"
                    value={contextKeywords}
                    onChange={(e) => setContextKeywords(e.target.value)}
                    className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-cyan-500 placeholder-slate-500"
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={handleSynthesizeContext}
                  disabled={synthesizingContext}
                  className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold px-4 py-2 rounded-lg text-xs flex items-center gap-2 transition"
                >
                  {synthesizingContext ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Sparkles className="w-3.5 h-3.5" />
                  )}
                  <span>Generate Bounded Context Bundle</span>
                </button>
              </div>

              {/* Synthesized Output Display */}
              {selectiveContext && (
                <div className="flex-1 overflow-y-auto space-y-3 pt-2">
                  <div className="flex items-center justify-between text-[11px] text-slate-400 border-b border-[#1e2738] pb-1.5">
                    <span>
                      Synthesized Items: <strong className="text-cyan-300">{selectiveContext.item_count}</strong> (Decisions: {selectiveContext.relevant_decisions.length}, Knowledge: {selectiveContext.relevant_knowledge.length}, Artifacts: {selectiveContext.relevant_artifacts.length})
                    </span>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(selectiveContext.synthesized_context);
                        setCopiedContext(true);
                        setTimeout(() => setCopiedContext(false), 2000);
                      }}
                      className="text-cyan-400 hover:text-white flex items-center gap-1 font-mono transition"
                    >
                      {copiedContext ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedContext ? "Copied!" : "Copy Context"}</span>
                    </button>
                  </div>

                  <pre className="p-4 rounded-xl bg-[#090d15] border border-[#1e2738] text-xs text-slate-200 font-mono whitespace-pre-wrap select-text leading-relaxed">
                    {selectiveContext.synthesized_context}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Create / Edit Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
            <div className="bg-[#0c1017] border border-[#1e2738] rounded-2xl max-w-xl w-full p-6 space-y-4 shadow-2xl relative max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between border-b border-[#1e2738] pb-3">
                <h3 className="text-sm font-bold text-white">
                  {editingItem ? "Edit Knowledge Record" : "Create New Knowledge Record"}
                </h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-slate-400 hover:text-white transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleSaveKnowledge} className="space-y-4 text-xs">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Title *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Microservices Boundary Architecture & Policy"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-cyan-500 placeholder-slate-500"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Category *</label>
                    <select
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value as KnowledgeCategory })}
                      className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-cyan-500"
                    >
                      {Object.keys(CATEGORY_CONFIG).map((cat) => (
                        <option key={cat} value={cat}>
                          {CATEGORY_CONFIG[cat].label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Confidence *</label>
                    <select
                      value={formData.confidence}
                      onChange={(e) =>
                        setFormData({ ...formData, confidence: e.target.value as KnowledgeConfidence })
                      }
                      className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-cyan-500"
                    >
                      <option value="HIGH">High Confidence</option>
                      <option value="MEDIUM">Medium Confidence</option>
                      <option value="LOW">Low Confidence</option>
                      <option value="ESTIMATED">Estimated</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Provenance Source Type</label>
                    <select
                      value={formData.source_type}
                      onChange={(e) =>
                        setFormData({ ...formData, source_type: e.target.value as KnowledgeSourceType })
                      }
                      className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-cyan-500"
                    >
                      <option value="RESEARCH">Research</option>
                      <option value="USER">User Operator</option>
                      <option value="AGENT">Autonomous Agent</option>
                      <option value="DOCUMENT">Document</option>
                      <option value="POST_MORTEM">Post Mortem</option>
                      <option value="MEETING">Meeting</option>
                      <option value="EXTERNAL">External</option>
                      <option value="SYSTEM">System</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Associated Project</label>
                    <select
                      value={formData.project_id}
                      onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                      className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-cyan-500"
                    >
                      <option value="">None (Company-Wide)</option>
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">Author Name (Optional)</label>
                  <input
                    type="text"
                    placeholder="Defaults to current operator or system agent"
                    value={formData.author_name}
                    onChange={(e) => setFormData({ ...formData, author_name: e.target.value })}
                    className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-cyan-500 placeholder-slate-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">Knowledge Content *</label>
                  <textarea
                    required
                    rows={6}
                    placeholder="Provide full description, rationale, benchmark findings, guidelines, or post-mortem notes..."
                    value={formData.content}
                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                    className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-cyan-500 placeholder-slate-500 font-sans"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Tags (comma-separated)</label>
                    <input
                      type="text"
                      placeholder="e.g. postgres, vector, guidelines"
                      value={formData.tags}
                      onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                      className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-cyan-500 placeholder-slate-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Source URI (Optional)</label>
                    <input
                      type="text"
                      placeholder="e.g. https://internal.wiki/page"
                      value={formData.source_uri}
                      onChange={(e) => setFormData({ ...formData, source_uri: e.target.value })}
                      className="w-full bg-[#111724] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-cyan-500 placeholder-slate-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">Metadata (JSON format)</label>
                  <textarea
                    rows={2}
                    value={formData.metadata_json}
                    onChange={(e) => setFormData({ ...formData, metadata_json: e.target.value })}
                    className="w-full bg-[#111724] border border-[#1e2738] text-xs text-slate-300 rounded-lg px-3 py-2 outline-none focus:border-cyan-500 font-mono"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-3 border-t border-[#1e2738]">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 rounded-lg bg-[#111724] hover:bg-[#161f30] text-slate-400 hover:text-white text-xs transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-semibold px-4 py-2 rounded-lg text-xs flex items-center gap-1.5 transition"
                  >
                    {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    <span>{editingItem ? "Save Changes" : "Create Record"}</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </ShellLayout>
  );
}
