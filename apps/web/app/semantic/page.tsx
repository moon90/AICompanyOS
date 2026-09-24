"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  BookOpen,
  Bot,
  Brain,
  Check,
  ChevronRight,
  Code2,
  Copy,
  Cpu,
  Database,
  ExternalLink,
  FileText,
  Filter,
  Layers,
  Lightbulb,
  Loader2,
  RefreshCw,
  Search,
  ShieldCheck,
  Sliders,
  Sparkles,
  Zap,
} from "lucide-react";
import {
  api,
  BatchIndexResponse,
  Company,
  Project,
  SemanticContextBuildResponse,
  SemanticSearchResultItem,
  SemanticSearchResponse,
  VectorMemoryStatsResponse,
} from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

const SOURCE_CONFIG: Record<
  string,
  { label: string; bg: string; text: string; border: string; icon: React.ComponentType<{ className?: string }> }
> = {
  KNOWLEDGE: {
    label: "Knowledge",
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/30",
    icon: BookOpen,
  },
  DECISION: {
    label: "Decision",
    bg: "bg-purple-500/10",
    text: "text-purple-400",
    border: "border-purple-500/30",
    icon: ShieldCheck,
  },
  ARTIFACT: {
    label: "Artifact",
    bg: "bg-cyan-500/10",
    text: "text-cyan-400",
    border: "border-cyan-500/30",
    icon: FileText,
  },
  TASK: {
    label: "Task",
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/30",
    icon: Check,
  },
};

const SAMPLE_QUERIES = [
  "PostgreSQL pgvector cosine distance operations",
  "Standardize on 768-dimensional dense embeddings",
  "Autonomous agent memory retrieval pipelines",
  "High accuracy HNSW cosine index configuration",
];

export default function SemanticMemoryPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Tab State
  const [activeTab, setActiveTab] = useState<"search" | "context" | "architecture">("search");

  // Telemetry & Stats
  const [stats, setStats] = useState<VectorMemoryStatsResponse | null>(null);
  const [reindexing, setReindexing] = useState(false);
  const [lastIndexResult, setLastIndexResult] = useState<BatchIndexResponse | null>(null);

  // Search Explorer State
  const [searchQuery, setSearchQuery] = useState("");
  const [minSimilarity, setMinSimilarity] = useState<number>(0.0);
  const [candidateLimit, setCandidateLimit] = useState<number>(6);
  const [selectedSources, setSelectedSources] = useState<string[]>(["KNOWLEDGE", "DECISION", "ARTIFACT", "TASK"]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<SemanticSearchResponse | null>(null);

  // Agent Context Simulator State
  const [contextPrompt, setContextPrompt] = useState("");
  const [contextLimit, setContextLimit] = useState<number>(5);
  const [contextMinSimilarity, setContextMinSimilarity] = useState<number>(0.05);
  const [contextAgentRole, setContextAgentRole] = useState("AI Architect");
  const [synthesizing, setSynthesizing] = useState(false);
  const [contextResult, setContextResult] = useState<SemanticContextBuildResponse | null>(null);
  const [copiedContext, setCopiedContext] = useState(false);

  // Initial Load: Companies
  useEffect(() => {
    async function loadCompanies() {
      try {
        setLoadingInitial(true);
        const res = await api.getCompanies();
        setCompanies(res);
        if (res.length > 0) {
          const stored = localStorage.getItem("selected_company_id");
          const target = res.find((c) => c.id === stored) || res[0];
          setSelectedCompanyId(target.id);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load companies");
      } finally {
        setLoadingInitial(false);
      }
    }
    loadCompanies();
  }, []);

  // Load Projects and Stats when Company Changes
  const loadStatsAndProjects = useCallback(async () => {
    if (!selectedCompanyId) return;
    try {
      const [projRes, statsRes] = await Promise.all([
        api.getProjects(selectedCompanyId).catch(() => ({ items: [], total: 0 })),
        api.getVectorMemoryStats(selectedCompanyId).catch(() => null),
      ]);
      setProjects(projRes.items || []);
      setStats(statsRes);
    } catch {
      // Graceful fallback
    }
  }, [selectedCompanyId]);

  useEffect(() => {
    loadStatsAndProjects();
  }, [loadStatsAndProjects]);

  // Handle Batch Reindex
  const handleBatchReindex = async () => {
    if (!selectedCompanyId || reindexing) return;
    try {
      setReindexing(true);
      setError(null);
      const res = await api.batchIndexMemory(selectedCompanyId, { force_reindex: true });
      setLastIndexResult(res);
      setSuccessMsg(`Vector memory successfully re-indexed ${res.indexed_count} items in ${res.duration_ms.toFixed(1)}ms!`);
      await loadStatsAndProjects();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Vector reindexing failed.");
    } finally {
      setReindexing(false);
    }
  };

  // Handle Semantic Search
  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!selectedCompanyId || !searchQuery.trim() || searching) return;
    try {
      setSearching(true);
      setError(null);
      const res = await api.searchSemanticMemory(selectedCompanyId, {
        query: searchQuery.trim(),
        limit: candidateLimit,
        min_similarity: minSimilarity,
        source_types: selectedSources.length > 0 ? selectedSources : undefined,
        project_id: selectedProjectId || undefined,
      });
      setSearchResults(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Semantic search inquiry failed.");
    } finally {
      setSearching(false);
    }
  };

  // Handle Context Synthesis
  const handleBuildAgentContext = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!selectedCompanyId || !contextPrompt.trim() || synthesizing) return;
    try {
      setSynthesizing(true);
      setError(null);
      const res = await api.buildSemanticContext(selectedCompanyId, {
        query: contextPrompt.trim(),
        limit: contextLimit,
        min_similarity: contextMinSimilarity,
        project_id: selectedProjectId || undefined,
      });
      setContextResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Context synthesis failed.");
    } finally {
      setSynthesizing(false);
    }
  };

  const handleCopyContext = () => {
    if (!contextResult) return;
    navigator.clipboard.writeText(contextResult.synthesized_context);
    setCopiedContext(true);
    setTimeout(() => setCopiedContext(false), 2000);
  };

  const toggleSource = (source: string) => {
    setSelectedSources((prev) =>
      prev.includes(source) ? prev.filter((s) => s !== source) : [...prev, source]
    );
  };

  return (
    <ShellLayout pageTitle="Vector Memory" breadcrumb="Organization & Intelligence">
      <div className="min-h-full bg-[#070a10] text-slate-100 p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Top Header & Telemetry */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-[#1e2738] pb-6">
          <div>
            <div className="flex items-center gap-2.5 mb-1.5">
              <div className="p-2 rounded-xl bg-gradient-to-br from-cyan-500/20 to-teal-500/20 border border-cyan-500/30 text-cyan-400">
                <Sparkles className="w-5 h-5 animate-pulse" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
                Vector / Semantic Memory
                <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                  Phase 20
                </span>
              </h1>
            </div>
            <p className="text-sm text-slate-400">
              Deterministic 768-dimensional dense vector retrieval with PostgreSQL pgvector HNSW indexing.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Company Selector */}
            <div className="relative">
              <select
                id="semantic-company-select"
                value={selectedCompanyId}
                onChange={(e) => {
                  setSelectedCompanyId(e.target.value);
                  localStorage.setItem("selected_company_id", e.target.value);
                  setSearchResults(null);
                  setContextResult(null);
                }}
                className="bg-[#0e1420] border border-[#1e2738] text-sm text-slate-200 rounded-lg px-3 py-2 pr-8 focus:outline-none focus:border-cyan-500"
              >
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Sync / Re-Index Button */}
            <button
              id="btn-reindex-all"
              onClick={handleBatchReindex}
              disabled={reindexing || !selectedCompanyId}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 text-white text-xs font-semibold shadow-lg shadow-cyan-900/30 transition disabled:opacity-50"
            >
              {reindexing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Embedding Vector Index...
                </>
              ) : (
                <>
                  <RefreshCw className="w-3.5 h-3.5" />
                  Sync &amp; Re-Index State
                </>
              )}
            </button>
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-xs hover:text-white">
              Dismiss
            </button>
          </div>
        )}

        {successMsg && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Check className="w-4 h-4 shrink-0 text-emerald-400" />
              <span>{successMsg}</span>
            </div>
            <button onClick={() => setSuccessMsg(null)} className="text-xs hover:text-white">
              Dismiss
            </button>
          </div>
        )}

        {/* Telemetry Stat Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-[#0c121d] border border-[#1e2738] relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition" />
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="font-medium">Total Vector Embeddings</span>
              <Layers className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {stats?.total_embeddings ?? 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Structured company chunks</p>
          </div>

          <div className="p-4 rounded-xl bg-[#0c121d] border border-[#1e2738] relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-teal-500/5 to-transparent opacity-0 group-hover:opacity-100 transition" />
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="font-medium">Embedding Dimension</span>
              <Cpu className="w-4 h-4 text-teal-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-teal-400">
              {stats?.dimension ?? 768}-dim
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Normalized dense vectors</p>
          </div>

          <div className="p-4 rounded-xl bg-[#0c121d] border border-[#1e2738] relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition" />
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="font-medium">Vector Index Topology</span>
              <Database className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-lg font-bold font-mono text-indigo-300">
              {stats?.index_type ?? "HNSW"}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">m=16, ef_construct=64</p>
          </div>

          <div className="p-4 rounded-xl bg-[#0c121d] border border-[#1e2738] relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 to-transparent opacity-0 group-hover:opacity-100 transition" />
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="font-medium">Source Distribution</span>
              <Zap className="w-4 h-4 text-amber-400" />
            </div>
            <div className="flex items-center gap-1.5 flex-wrap mt-1">
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                KN:{stats?.count_by_source?.KNOWLEDGE ?? 0}
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                DEC:{stats?.count_by_source?.DECISION ?? 0}
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                ART:{stats?.count_by_source?.ARTIFACT ?? 0}
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                TSK:{stats?.count_by_source?.TASK ?? 0}
              </span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-[#1e2738] text-sm">
          <button
            id="tab-btn-search"
            onClick={() => setActiveTab("search")}
            className={`flex items-center gap-2 px-4 py-2.5 font-medium border-b-2 transition ${
              activeTab === "search"
                ? "border-cyan-500 text-cyan-400 bg-cyan-500/5"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Search className="w-4 h-4" />
            Semantic Search Explorer
          </button>

          <button
            id="tab-btn-context"
            onClick={() => setActiveTab("context")}
            className={`flex items-center gap-2 px-4 py-2.5 font-medium border-b-2 transition ${
              activeTab === "context"
                ? "border-cyan-500 text-cyan-400 bg-cyan-500/5"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Brain className="w-4 h-4" />
            Agent Context Builder
          </button>

          <button
            id="tab-btn-architecture"
            onClick={() => setActiveTab("architecture")}
            className={`flex items-center gap-2 px-4 py-2.5 font-medium border-b-2 transition ${
              activeTab === "architecture"
                ? "border-cyan-500 text-cyan-400 bg-cyan-500/5"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Database className="w-4 h-4" />
            pgvector Architecture &amp; Governance
          </button>
        </div>

        {/* TAB 1: Semantic Search Explorer */}
        {activeTab === "search" && (
          <div className="space-y-6">
            {/* Search Input Box */}
            <form onSubmit={handleSearch} className="p-5 rounded-2xl bg-[#0c121d] border border-[#1e2738] space-y-4">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
                  <input
                    id="semantic-search-input"
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Enter natural language inquiry (e.g., PostgreSQL pgvector deployment standards)..."
                    className="w-full bg-[#080d16] border border-[#1e2738] rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  />
                </div>
                <button
                  id="btn-run-search"
                  type="submit"
                  disabled={searching || !searchQuery.trim()}
                  className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold flex items-center justify-center gap-2 shadow-lg shadow-cyan-900/30 transition disabled:opacity-50"
                >
                  {searching ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Scanning...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      Vector Scan
                    </>
                  )}
                </button>
              </div>

              {/* Sample Queries */}
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                  Quick Inquiries:
                </span>
                {SAMPLE_QUERIES.map((q, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setSearchQuery(q);
                    }}
                    className="text-[11px] px-2.5 py-1 rounded-full bg-[#111726] border border-[#1e2738] text-slate-300 hover:text-cyan-300 hover:border-cyan-500/40 transition"
                  >
                    {q}
                  </button>
                ))}
              </div>

              {/* Advanced Filter Bar */}
              <div className="pt-3 border-t border-[#1e2738] flex flex-wrap items-center justify-between gap-4">
                {/* Source Selection Chips */}
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs text-slate-400 flex items-center gap-1 mr-1">
                    <Filter className="w-3.5 h-3.5" />
                    Sources:
                  </span>
                  {(["KNOWLEDGE", "DECISION", "ARTIFACT", "TASK"] as const).map((src) => {
                    const active = selectedSources.includes(src);
                    const cfg = SOURCE_CONFIG[src];
                    return (
                      <button
                        key={src}
                        type="button"
                        onClick={() => toggleSource(src)}
                        className={`text-xs px-2.5 py-1 rounded-lg border transition flex items-center gap-1.5 ${
                          active
                            ? `${cfg.bg} ${cfg.text} ${cfg.border}`
                            : "bg-[#080d16] text-slate-400 border-[#1e2738] opacity-60 hover:opacity-100"
                        }`}
                      >
                        <cfg.icon className="w-3 h-3" />
                        {cfg.label}
                      </button>
                    );
                  })}
                </div>

                {/* Sliders & Project Scope */}
                <div className="flex flex-wrap items-center gap-4 text-xs">
                  {/* Min Similarity Slider */}
                  <div className="flex items-center gap-2">
                    <Sliders className="w-3.5 h-3.5 text-cyan-400" />
                    <span className="text-slate-400">Min Similarity:</span>
                    <input
                      id="min-similarity-slider"
                      type="range"
                      min="-0.5"
                      max="0.9"
                      step="0.05"
                      value={minSimilarity}
                      onChange={(e) => setMinSimilarity(parseFloat(e.target.value))}
                      className="w-24 accent-cyan-500"
                    />
                    <span className="font-mono text-cyan-300 w-10">{minSimilarity.toFixed(2)}</span>
                  </div>

                  {/* Limit Select */}
                  <div className="flex items-center gap-1.5">
                    <span className="text-slate-400">Limit:</span>
                    <select
                      id="candidate-limit-select"
                      value={candidateLimit}
                      onChange={(e) => setCandidateLimit(parseInt(e.target.value, 10))}
                      className="bg-[#080d16] border border-[#1e2738] rounded px-2 py-1 text-slate-300 focus:outline-none focus:border-cyan-500"
                    >
                      <option value="3">3</option>
                      <option value="6">6</option>
                      <option value="10">10</option>
                      <option value="15">15</option>
                    </select>
                  </div>
                </div>
              </div>
            </form>

            {/* Results Grid */}
            {searchResults && (
              <div className="space-y-4">
                <div className="flex items-center justify-between text-xs text-slate-400 px-1">
                  <span>
                    Found <strong className="text-white">{searchResults.total_matches}</strong> semantic candidate matches
                    in <strong className="text-cyan-400 font-mono">{searchResults.execution_time_ms.toFixed(1)}ms</strong>
                  </span>
                  <span className="font-mono text-[11px]">HNSW vector_cosine_ops</span>
                </div>

                {searchResults.results.length === 0 ? (
                  <div className="p-8 text-center rounded-2xl bg-[#0c121d] border border-[#1e2738] text-slate-400 space-y-2">
                    <p className="text-sm font-medium text-slate-300">No candidates exceeded similarity threshold.</p>
                    <p className="text-xs text-slate-400">
                      Try lowering the minimum similarity score or re-indexing company knowledge.
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {searchResults.results.map((item) => {
                      const cfg = SOURCE_CONFIG[item.source_type] || {
                        label: item.source_type,
                        bg: "bg-slate-500/10",
                        text: "text-slate-300",
                        border: "border-slate-500/30",
                        icon: Database,
                      };
                      const similarityPercent = Math.max(0, Math.min(100, Math.round(item.similarity_score * 100)));

                      return (
                        <div
                          key={item.id}
                          className="p-5 rounded-2xl bg-[#0c121d] border border-[#1e2738] hover:border-cyan-500/40 transition flex flex-col justify-between space-y-3"
                        >
                          <div>
                            {/* Card Header: Source & Similarity Gauge */}
                            <div className="flex items-center justify-between gap-2 mb-2">
                              <span
                                className={`text-[11px] font-mono px-2 py-0.5 rounded border inline-flex items-center gap-1.5 ${cfg.bg} ${cfg.text} ${cfg.border}`}
                              >
                                <cfg.icon className="w-3 h-3" />
                                {cfg.label} #{item.source_id.slice(-6)}
                              </span>

                              <div className="flex items-center gap-2">
                                <div className="w-20 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                                  <div
                                    className="h-full bg-gradient-to-r from-teal-500 to-cyan-400 rounded-full"
                                    style={{ width: `${similarityPercent}%` }}
                                  />
                                </div>
                                <span className="text-xs font-mono font-bold text-cyan-400">
                                  {(item.similarity_score * 100).toFixed(1)}%
                                </span>
                              </div>
                            </div>

                            {/* Title */}
                            <h3 className="text-sm font-semibold text-white tracking-tight leading-snug">
                              {item.title}
                            </h3>

                            {/* Excerpt */}
                            <p className="text-xs text-slate-300 leading-relaxed mt-2 whitespace-pre-line line-clamp-4">
                              {item.content_chunk}
                            </p>
                          </div>

                          {/* Card Footer: Metadata snippet */}
                          <div className="pt-2 border-t border-[#1e2738]/60 flex items-center justify-between text-[11px] text-slate-400">
                            <span className="font-mono">Distance: {item.distance.toFixed(4)}</span>
                            {item.metadata?.category ? (
                              <span className="text-slate-400">Category: {String(item.metadata.category)}</span>
                            ) : null}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: Agent Context Builder Simulator */}
        {activeTab === "context" && (
          <div className="space-y-6">
            <div className="p-5 rounded-2xl bg-[#0c121d] border border-[#1e2738] space-y-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <Brain className="w-4 h-4 text-cyan-400" />
                <span>Simulate Agent Context Injection (docs/Memory.md § 40)</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Before an agent executes a task, AI Company OS executes a selective semantic retrieval pass across
                the company vector store. This synthesizes a bounded markdown context containing strictly relevant
                precedents and policies without blowing up token budgets.
              </p>

              <form onSubmit={handleBuildAgentContext} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">
                      Target Agent Persona
                    </label>
                    <select
                      id="context-agent-role"
                      value={contextAgentRole}
                      onChange={(e) => setContextAgentRole(e.target.value)}
                      className="w-full bg-[#080d16] border border-[#1e2738] rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                    >
                      <option value="AI Principal Architect">AI Principal Architect</option>
                      <option value="Lead Software Engineer">Lead Software Engineer</option>
                      <option value="DevOps & Reliability Engineer">DevOps &amp; Reliability Engineer</option>
                      <option value="QA & Security Auditor">QA &amp; Security Auditor</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">
                      Max Injected Chunks
                    </label>
                    <select
                      id="context-limit-select"
                      value={contextLimit}
                      onChange={(e) => setContextLimit(parseInt(e.target.value, 10))}
                      className="w-full bg-[#080d16] border border-[#1e2738] rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                    >
                      <option value="3">Top 3 Most Relevant Chunks</option>
                      <option value="5">Top 5 Most Relevant Chunks</option>
                      <option value="8">Top 8 Most Relevant Chunks</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Task Statement / Agent Prompt
                  </label>
                  <textarea
                    id="context-task-prompt"
                    rows={3}
                    value={contextPrompt}
                    onChange={(e) => setContextPrompt(e.target.value)}
                    placeholder="Describe the task or question the agent will execute..."
                    className="w-full bg-[#080d16] border border-[#1e2738] rounded-xl p-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-slate-400">Min Similarity:</span>
                    <input
                      id="context-min-sim-slider"
                      type="range"
                      min="-0.2"
                      max="0.8"
                      step="0.05"
                      value={contextMinSimilarity}
                      onChange={(e) => setContextMinSimilarity(parseFloat(e.target.value))}
                      className="w-24 accent-cyan-500"
                    />
                    <span className="font-mono text-cyan-300">{contextMinSimilarity.toFixed(2)}</span>
                  </div>

                  <button
                    id="btn-build-context"
                    type="submit"
                    disabled={synthesizing || !contextPrompt.trim()}
                    className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-500 hover:to-cyan-500 text-white text-sm font-semibold flex items-center gap-2 shadow-lg shadow-teal-900/30 transition disabled:opacity-50"
                  >
                    {synthesizing ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Synthesizing Context...
                      </>
                    ) : (
                      <>
                        <Code2 className="w-4 h-4" />
                        Synthesize Context
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* Synthesized Output Preview */}
            {contextResult && (
              <div className="p-5 rounded-2xl bg-[#0c121d] border border-[#1e2738] space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-slate-300">
                    <span className="font-semibold text-white">Synthesized Context Output</span>
                    <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 font-mono text-[11px]">
                      {contextResult.total_items} chunks used
                    </span>
                  </div>
                  <button
                    id="btn-copy-context"
                    onClick={handleCopyContext}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#111726] border border-[#1e2738] text-xs text-slate-300 hover:text-white transition"
                  >
                    {copiedContext ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        Copy Markdown
                      </>
                    )}
                  </button>
                </div>

                <div className="relative">
                  <pre className="p-4 rounded-xl bg-[#080d16] border border-[#1e2738] text-xs font-mono text-cyan-200/90 whitespace-pre-wrap leading-relaxed overflow-x-auto max-h-96">
                    {contextResult.synthesized_context}
                  </pre>
                </div>

                {/* Used Items Breakdown */}
                {contextResult.items_used.length > 0 && (
                  <div className="pt-3 border-t border-[#1e2738]">
                    <h4 className="text-xs font-semibold text-slate-400 mb-2">Grounded Source Chunks Injected:</h4>
                    <div className="flex flex-wrap gap-2">
                      {contextResult.items_used.map((item) => (
                        <div
                          key={item.id}
                          className="px-2.5 py-1 rounded bg-[#080d16] border border-[#1e2738] text-[11px] flex items-center gap-2"
                        >
                          <span className="text-slate-400 font-mono">[{item.source_type}]</span>
                          <span className="text-slate-200">{item.title}</span>
                          <span className="text-cyan-400 font-mono">{(item.similarity_score * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: Architecture & Governance */}
        {activeTab === "architecture" && (
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-[#0c121d] border border-[#1e2738] space-y-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <Database className="w-4 h-4 text-cyan-400" />
                <span>Architectural Principle: Vector Memory as Retrieval Mechanism</span>
              </div>
              <blockquote className="border-l-2 border-cyan-500 pl-4 py-1 text-sm text-cyan-200 italic font-serif">
                “Vector memory is a retrieval mechanism. It is NOT the authoritative source of company state.
                Structured truth remains in PostgreSQL; temporary operational state lives in Redis; pgvector enables semantic retrieval.”
                <footer className="text-xs text-slate-400 not-italic font-sans mt-1">— docs/Memory.md § 40</footer>
              </blockquote>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
                <div className="p-4 rounded-xl bg-[#080d16] border border-[#1e2738] space-y-2">
                  <h4 className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                    <Database className="w-3.5 h-3.5 text-indigo-400" />
                    Structured Truth (PostgreSQL)
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Authoritative ACID transactions, state machines, relational integrity, audit trails, and security policies.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-[#080d16] border border-[#1e2738] space-y-2">
                  <h4 className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                    Semantic Retrieval (pgvector)
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    768-dimensional dense vector embeddings with HNSW indexing (vector_cosine_ops) for high-speed nearest-neighbor search.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-[#080d16] border border-[#1e2738] space-y-2">
                  <h4 className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                    <Zap className="w-3.5 h-3.5 text-amber-400" />
                    Operational Cache (Redis)
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Temporary execution locks, real-time presence heartbeats, pub/sub streams, and transient session caches.
                  </p>
                </div>
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-[#0c121d] border border-[#1e2738] space-y-3">
              <h3 className="text-sm font-semibold text-white">Continuous Memory Ingestion Pipeline</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                As AI agents and users create knowledge items, record decisions, commit artifacts, or complete tasks,
                embeddings are generated and synchronized with PostgreSQL pgvector tables. The system ensures zero
                vector data drift with the underlying relational models.
              </p>
            </div>
          </div>
        )}
      </div>
    </ShellLayout>
  );
}
