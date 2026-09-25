"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Cpu,
  FileCheck,
  FileText,
  Filter,
  Layers,
  ListChecks,
  Loader2,
  Play,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Target,
  Terminal,
  XCircle,
} from "lucide-react";
import {
  api,
  BenchmarkCategory,
  BenchmarkDefinitionResponse,
  BenchmarkRunResponse,
  Company,
  CriterionType,
  PipelineStage,
  VerificationRunResponse,
  VerificationStatus,
  VerificationTelemetryResponse,
} from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

// Canonical 8 Evaluation Dimensions with descriptions and badge colors
const DIMENSIONS_CONFIG: Record<
  CriterionType,
  { label: string; description: string; icon: string; color: string; border: string; bg: string }
> = {
  CORRECTNESS: {
    label: "Correctness",
    description: "Factual consistency and execution output accuracy.",
    icon: "🎯",
    color: "text-emerald-400",
    border: "border-emerald-500/30",
    bg: "bg-emerald-500/10",
  },
  COMPLETENESS: {
    label: "Completeness",
    description: "Fulfillment of all required task deliverables and outputs.",
    icon: "📦",
    color: "text-blue-400",
    border: "border-blue-500/30",
    bg: "bg-blue-500/10",
  },
  TOOL_USAGE: {
    label: "Tool Usage",
    description: "Correct invocation, parameterization, and output handling of external tools.",
    icon: "🔧",
    color: "text-indigo-400",
    border: "border-indigo-500/30",
    bg: "bg-indigo-500/10",
  },
  PERMISSION_COMPLIANCE: {
    label: "Permission Compliance",
    description: "Adherence to role authority, approval barriers, and tenant separation.",
    icon: "🛡️",
    color: "text-purple-400",
    border: "border-purple-500/30",
    bg: "bg-purple-500/10",
  },
  HALLUCINATION_RATE: {
    label: "Hallucination Control",
    description: "Verification that outputs are grounded in system artifacts and databases.",
    icon: "🔍",
    color: "text-amber-400",
    border: "border-amber-500/30",
    bg: "bg-amber-500/10",
  },
  INSTRUCTION_FOLLOWING: {
    label: "Instruction Following",
    description: "Strict adherence to constraints, policies, and operational prompts.",
    icon: "📋",
    color: "text-cyan-400",
    border: "border-cyan-500/30",
    bg: "bg-cyan-500/10",
  },
  TASK_COMPLETION: {
    label: "Task Completion",
    description: "Definitive state achievement and deliverable generation.",
    icon: "🏁",
    color: "text-teal-400",
    border: "border-teal-500/30",
    bg: "bg-teal-500/10",
  },
  EVIDENCE_QUALITY: {
    label: "Evidence Quality",
    description: "Rule 146 verifiable source citations, audit diffs, and execution logs.",
    icon: "📑",
    color: "text-rose-400",
    border: "border-rose-500/30",
    bg: "bg-rose-500/10",
  },
};

// 5-Stage Verification Pipeline definitions adhering to docs/Architecture.md § 71
const PIPELINE_STAGES: { stage: PipelineStage; title: string; subtitle: string; icon: any }[] = [
  {
    stage: "SCHEMA_VALIDATION",
    title: "1. Schema Validation",
    subtitle: "Deliverable shape & structure",
    icon: ListChecks,
  },
  {
    stage: "EVIDENCE_CHECK",
    title: "2. Evidence Check",
    subtitle: "Rule 146 source & log citations",
    icon: FileCheck,
  },
  {
    stage: "TASK_VERIFICATION",
    title: "3. Task Verification",
    subtitle: "Code, tool & artifact audit",
    icon: Cpu,
  },
  {
    stage: "EVALUATION",
    title: "4. Multi-Dim Evaluation",
    subtitle: "8 canonical quality dimensions",
    icon: Target,
  },
  {
    stage: "COMPLETED",
    title: "5. Verified State",
    subtitle: "Rule 17 gate: score ≥ 80.0",
    icon: ShieldCheck,
  },
];

const CATEGORY_COLORS: Record<BenchmarkCategory, { bg: string; text: string; border: string }> = {
  CEO: { bg: "bg-amber-500/15", text: "text-amber-400", border: "border-amber-500/30" },
  MARKETING: { bg: "bg-pink-500/15", text: "text-pink-400", border: "border-pink-500/30" },
  ENGINEERING: { bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30" },
  SALES: { bg: "bg-emerald-500/15", text: "text-emerald-400", border: "border-emerald-500/30" },
  TOOL: { bg: "bg-indigo-500/15", text: "text-indigo-400", border: "border-indigo-500/30" },
  APPROVAL: { bg: "bg-rose-500/15", text: "text-rose-400", border: "border-rose-500/30" },
  FAILURE: { bg: "bg-red-500/15", text: "text-red-400", border: "border-red-500/30" },
  RECOVERY: { bg: "bg-teal-500/15", text: "text-teal-400", border: "border-teal-500/30" },
};

export default function VerificationPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [telemetry, setTelemetry] = useState<VerificationTelemetryResponse | null>(null);
  const [runs, setRuns] = useState<VerificationRunResponse[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarkDefinitionResponse[]>([]);
  const [selectedRun, setSelectedRun] = useState<VerificationRunResponse | null>(null);

  // Active navigation tab
  const [activeTab, setActiveTab] = useState<"pipeline" | "radar" | "benchmarks" | "runs">("pipeline");

  // Form states for manual verifier
  const [targetType, setTargetType] = useState<"TASK" | "ARTIFACT">("TASK");
  const [targetIdInput, setTargetIdInput] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  // Benchmark execution state
  const [runningBenchmarkId, setRunningBenchmarkId] = useState<string | null>(null);
  const [benchmarkResult, setBenchmarkResult] = useState<BenchmarkRunResponse | null>(null);

  // Historical runs filter
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const loadData = useCallback(async (compId: string) => {
    try {
      setLoading(true);
      const [telemRes, runsRes, bmkRes] = await Promise.all([
        api.getVerificationTelemetry(compId).catch(() => null),
        api.listVerificationRuns(compId, { limit: 50 }).catch(() => ({ items: [], total: 0 })),
        api.listBenchmarks(compId).catch(() => []),
      ]);
      setTelemetry(telemRes);
      setRuns(runsRes.items);
      setBenchmarks(bmkRes);

      if (runsRes.items.length > 0 && !selectedRun) {
        setSelectedRun(runsRes.items[0]);
      }
    } catch (err: any) {
      console.error("Failed to load verification data:", err);
    } finally {
      setLoading(false);
    }
  }, [selectedRun]);

  useEffect(() => {
    async function init() {
      try {
        const comps = await api.getCompanies();
        setCompanies(comps);
        if (comps.length > 0) {
          const compId = comps[0].id;
          setSelectedCompanyId(compId);
          await loadData(compId);
        }
      } catch (err) {
        console.error("Failed to initialize companies:", err);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, [loadData]);

  const handleCompanyChange = async (compId: string) => {
    setSelectedCompanyId(compId);
    await loadData(compId);
  };

  const handleRunVerification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetIdInput.trim() || !selectedCompanyId) return;

    setIsVerifying(true);
    setVerifyError(null);

    try {
      let res: VerificationRunResponse;
      if (targetType === "TASK") {
        res = await api.verifyTask(selectedCompanyId, targetIdInput.trim());
      } else {
        res = await api.verifyArtifact(selectedCompanyId, targetIdInput.trim());
      }
      setSelectedRun(res);
      setRuns((prev) => [res, ...prev]);
      // Refresh telemetry
      const updatedTelem = await api.getVerificationTelemetry(selectedCompanyId).catch(() => null);
      if (updatedTelem) setTelemetry(updatedTelem);
    } catch (err: any) {
      setVerifyError(err?.detail || err?.message || "Verification failed to complete.");
    } finally {
      setIsVerifying(false);
    }
  };

  const handleExecuteBenchmark = async (benchmark: BenchmarkDefinitionResponse) => {
    if (!selectedCompanyId) return;
    setRunningBenchmarkId(benchmark.id);
    setBenchmarkResult(null);

    try {
      const res = await api.runEvaluationBenchmark(selectedCompanyId, {
        category: benchmark.category,
        prompt: benchmark.canonical_prompt,
      });
      setBenchmarkResult(res);
      setSelectedRun(res.verification_run);
      setRuns((prev) => [res.verification_run, ...prev]);
      const updatedTelem = await api.getVerificationTelemetry(selectedCompanyId).catch(() => null);
      if (updatedTelem) setTelemetry(updatedTelem);
    } catch (err: any) {
      console.error("Benchmark run failed:", err);
    } finally {
      setRunningBenchmarkId(null);
    }
  };

  const filteredRuns = runs.filter((r) => {
    const matchesStatus = statusFilter === "ALL" || r.status === statusFilter;
    const matchesSearch =
      !searchQuery.trim() ||
      r.target_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.summary && r.summary.toLowerCase().includes(searchQuery.toLowerCase())) ||
      r.target_type.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <ShellLayout pageTitle="AI Verification & Eval" breadcrumb="System & Governance">
      <div className="flex-1 flex flex-col h-full bg-[#0a0e17] text-slate-100 overflow-y-auto">
        {/* Top Header Banner */}
        <header className="border-b border-[#1e2738] bg-[#0c121e]/80 backdrop-blur-md px-6 py-4 sticky top-0 z-20">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 max-w-7xl mx-auto">
            <div>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                    AI Verification &amp; Evaluation Engine
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      Phase 22 Active
                    </span>
                  </h1>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Automated 5-stage pipeline, Rule 17 independent completion gate &amp; 8-dimensional evaluation scorecard.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <select
                aria-label="Select Company"
                value={selectedCompanyId}
                onChange={(e) => handleCompanyChange(e.target.value)}
                className="bg-[#111827] border border-[#1e2738] text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>

              <button
                onClick={() => selectedCompanyId && loadData(selectedCompanyId)}
                className="p-1.5 text-slate-400 hover:text-slate-200 bg-[#111827] border border-[#1e2738] rounded-lg transition"
                title="Refresh verification data"
                aria-label="Refresh Data"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>

          {/* Quick Metrics Ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 max-w-7xl mx-auto">
            <div className="bg-[#101726]/60 border border-[#1e2738] rounded-lg p-3 flex items-center gap-3">
              <div className="p-2 rounded-md bg-blue-500/10 text-blue-400">
                <Activity className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[11px] text-slate-400 font-mono">TOTAL VERIFICATIONS</div>
                <div className="text-base font-semibold text-white">
                  {telemetry?.total_runs ?? runs.length}
                </div>
              </div>
            </div>

            <div className="bg-[#101726]/60 border border-[#1e2738] rounded-lg p-3 flex items-center gap-3">
              <div className="p-2 rounded-md bg-emerald-500/10 text-emerald-400">
                <CheckCircle2 className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[11px] text-slate-400 font-mono">PASS RATE</div>
                <div className="text-base font-semibold text-emerald-400">
                  {telemetry ? `${telemetry.pass_rate_percent}%` : "—"}
                </div>
              </div>
            </div>

            <div className="bg-[#101726]/60 border border-[#1e2738] rounded-lg p-3 flex items-center gap-3">
              <div className="p-2 rounded-md bg-purple-500/10 text-purple-400">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[11px] text-slate-400 font-mono">AVG OVERALL SCORE</div>
                <div className="text-base font-semibold text-purple-300">
                  {telemetry ? `${telemetry.avg_overall_score} / 100` : "—"}
                </div>
              </div>
            </div>

            <div className="bg-[#101726]/60 border border-[#1e2738] rounded-lg p-3 flex items-center gap-3">
              <div className="p-2 rounded-md bg-amber-500/10 text-amber-400">
                <Target className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[11px] text-slate-400 font-mono">BENCHMARK SUITES</div>
                <div className="text-base font-semibold text-amber-300">
                  {benchmarks.length} Active Categories
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 mt-4 border-b border-transparent max-w-7xl mx-auto">
            <button
              onClick={() => setActiveTab("pipeline")}
              className={`px-3 py-1.5 text-xs font-medium rounded-t-lg transition border-b-2 flex items-center gap-1.5 ${
                activeTab === "pipeline"
                  ? "border-emerald-500 text-emerald-400 bg-emerald-500/10"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              5-Stage Pipeline Verifier
            </button>

            <button
              onClick={() => setActiveTab("radar")}
              className={`px-3 py-1.5 text-xs font-medium rounded-t-lg transition border-b-2 flex items-center gap-1.5 ${
                activeTab === "radar"
                  ? "border-indigo-500 text-indigo-400 bg-indigo-500/10"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
              }`}
            >
              <Target className="w-3.5 h-3.5" />
              8-Dimensional Scorecard
            </button>

            <button
              onClick={() => setActiveTab("benchmarks")}
              className={`px-3 py-1.5 text-xs font-medium rounded-t-lg transition border-b-2 flex items-center gap-1.5 ${
                activeTab === "benchmarks"
                  ? "border-amber-500 text-amber-400 bg-amber-500/10"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              Benchmark Suite Runner
            </button>

            <button
              onClick={() => setActiveTab("runs")}
              className={`px-3 py-1.5 text-xs font-medium rounded-t-lg transition border-b-2 flex items-center gap-1.5 ${
                activeTab === "runs"
                  ? "border-cyan-500 text-cyan-400 bg-cyan-500/10"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              Audit Log &amp; Runs ({runs.length})
            </button>
          </div>
        </header>

        {/* Tab Content Area */}
        <main className="p-6 max-w-7xl mx-auto w-full space-y-6 flex-1">
          {/* TAB 1: 5-Stage Verification Pipeline */}
          {activeTab === "pipeline" && (
            <div className="space-y-6">
              {/* Pipeline Architecture Diagram */}
              <div className="bg-[#111724]/90 border border-[#1e2738] rounded-xl p-5 shadow-xl">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                      <Layers className="w-4 h-4 text-emerald-400" />
                      5-Stage Autonomous Verification Pipeline
                    </h2>
                    <p className="text-xs text-slate-400">
                      Enforcing Rule 17: Tasks and artifacts never transition to VERIFIED without automated multi-stage evaluation.
                    </p>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-emerald-500/40 bg-emerald-500/10 text-emerald-300">
                    Threshold: ≥ 80.0 / 100
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                  {PIPELINE_STAGES.map((s, idx) => {
                    const Icon = s.icon;
                    const isSelectedRunStage = selectedRun?.pipeline_stage === s.stage;
                    const isPassed =
                      selectedRun &&
                      (selectedRun.pipeline_stage === "COMPLETED" ||
                        (selectedRun.status === "PASSED" && idx <= 4));

                    return (
                      <div
                        key={s.stage}
                        className={`p-3.5 rounded-lg border transition-all ${
                          isSelectedRunStage
                            ? "bg-indigo-950/30 border-indigo-500/60 shadow-lg shadow-indigo-500/10 ring-1 ring-indigo-500/30"
                            : isPassed
                            ? "bg-emerald-950/20 border-emerald-500/40"
                            : "bg-[#0d121c] border-[#1e2738]"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[10px] font-mono text-slate-300">STEP {idx + 1}</span>
                          <Icon
                            className={`w-4 h-4 ${
                              isSelectedRunStage
                                ? "text-indigo-400 animate-pulse"
                                : isPassed
                                ? "text-emerald-400"
                                : "text-slate-300"
                            }`}
                          />
                        </div>
                        <h4 className="text-xs font-semibold text-white leading-tight">{s.title}</h4>
                        <p className="text-[11px] text-slate-400 mt-1 leading-snug">{s.subtitle}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Trigger Manual Verification Box */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="bg-[#111724]/90 border border-[#1e2738] rounded-xl p-5 shadow-xl space-y-4">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <Play className="w-4 h-4 text-indigo-400" />
                    Trigger Evaluation Harness
                  </h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Verify a task execution record or artifact content against the 8 canonical dimensions and empirical citations.
                  </p>

                  <form onSubmit={handleRunVerification} className="space-y-4">
                    <div>
                      <label className="text-[11px] font-mono text-slate-300 block mb-1">
                        TARGET TYPE
                      </label>
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          type="button"
                          onClick={() => setTargetType("TASK")}
                          className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition flex items-center justify-center gap-1.5 ${
                            targetType === "TASK"
                              ? "bg-indigo-600/20 text-indigo-300 border-indigo-500/40"
                              : "bg-[#0d121c] text-slate-400 border-[#1e2738] hover:text-white"
                          }`}
                        >
                          <Terminal className="w-3.5 h-3.5" />
                          Task Execution
                        </button>
                        <button
                          type="button"
                          onClick={() => setTargetType("ARTIFACT")}
                          className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition flex items-center justify-center gap-1.5 ${
                            targetType === "ARTIFACT"
                              ? "bg-indigo-600/20 text-indigo-300 border-indigo-500/40"
                              : "bg-[#0d121c] text-slate-400 border-[#1e2738] hover:text-white"
                          }`}
                        >
                          <FileText className="w-3.5 h-3.5" />
                          Artifact / Doc
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="text-[11px] font-mono text-slate-300 block mb-1">
                        TARGET ID ({targetType === "TASK" ? "Task UUID" : "Artifact UUID"})
                      </label>
                      <input
                        type="text"
                        value={targetIdInput}
                        onChange={(e) => setTargetIdInput(e.target.value)}
                        placeholder={
                          targetType === "TASK"
                            ? "e.g. tsk-0193498a-..."
                            : "e.g. art-0193498a-..."
                        }
                        className="w-full bg-[#0d121c] border border-[#1e2738] text-xs text-white rounded-lg px-3 py-2 font-mono placeholder:text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        required
                      />
                    </div>

                    {verifyError && (
                      <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 shrink-0" />
                        <span>{verifyError}</span>
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={isVerifying || !targetIdInput.trim()}
                      className="w-full py-2 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition disabled:opacity-50"
                    >
                      {isVerifying ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Evaluating 5 Stages...
                        </>
                      ) : (
                        <>
                          <ShieldCheck className="w-4 h-4" />
                          Execute Verification Pipeline
                        </>
                      )}
                    </button>
                  </form>
                </div>

                {/* Selected Run Inspection Inspector */}
                <div className="lg:col-span-2 bg-[#111724]/90 border border-[#1e2738] rounded-xl p-5 shadow-xl flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between pb-3 border-b border-[#1e2738]">
                      <div className="flex items-center gap-2.5">
                        <span
                          className={`text-xs font-mono font-semibold px-2.5 py-0.5 rounded-full border ${
                            selectedRun?.status === "PASSED"
                              ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
                              : selectedRun?.status === "FAILED"
                              ? "bg-rose-500/15 text-rose-400 border-rose-500/30"
                              : "bg-amber-500/15 text-amber-400 border-amber-500/30"
                          }`}
                        >
                          {selectedRun?.status || "NO SELECTION"}
                        </span>
                        <span className="text-xs font-mono text-slate-400">
                          {selectedRun ? `Target: ${selectedRun.target_type} #${selectedRun.target_id}` : "Select a run to inspect"}
                        </span>
                      </div>

                      {selectedRun && (
                        <div className="text-right">
                          <span className="text-lg font-bold text-white">
                            {selectedRun.overall_score}
                          </span>
                          <span className="text-xs text-slate-300 font-mono"> / 100</span>
                        </div>
                      )}
                    </div>

                    {selectedRun ? (
                      <div className="mt-4 space-y-4">
                        <div className="p-3 rounded-lg bg-[#0d121c] border border-[#1e2738] text-xs text-slate-300">
                          <span className="font-semibold text-white block mb-1">Audit Summary:</span>
                          <p className="leading-relaxed text-slate-400">{selectedRun.summary || "No summary notes recorded."}</p>
                        </div>

                        {/* Criteria Breakdown Grid */}
                        <div>
                          <h4 className="text-xs font-mono uppercase text-slate-300 tracking-wider mb-2">
                            Dimension Scores &amp; Citations:
                          </h4>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                            {selectedRun.criteria_scores.map((cs) => {
                              const dimInfo = DIMENSIONS_CONFIG[cs.criterion];
                              return (
                                <div
                                  key={cs.id}
                                  className="p-2.5 rounded-lg bg-[#0d121c] border border-[#1e2738] flex flex-col justify-between"
                                >
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs font-medium text-white flex items-center gap-1.5">
                                      <span>{dimInfo?.icon || "📊"}</span>
                                      {dimInfo?.label || cs.criterion}
                                    </span>
                                    <span
                                      className={`text-xs font-mono font-bold ${
                                        cs.score >= 80 ? "text-emerald-400" : cs.score >= 60 ? "text-amber-400" : "text-rose-400"
                                      }`}
                                    >
                                      {cs.score}
                                    </span>
                                  </div>
                                  <p className="text-[11px] text-slate-400 line-clamp-2">
                                    {cs.details || dimInfo?.description}
                                  </p>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="h-48 flex flex-col items-center justify-center text-slate-300 text-xs">
                        <ShieldAlert className="w-8 h-8 mb-2 opacity-50" />
                        No verification run selected. Run a verification or pick from history below.
                      </div>
                    )}
                  </div>

                  {selectedRun && (
                    <div className="mt-4 pt-3 border-t border-[#1e2738] flex items-center justify-between text-[11px] text-slate-300 font-mono">
                      <span>Started: {new Date(selectedRun.started_at).toLocaleTimeString()}</span>
                      <span>Run ID: {selectedRun.id}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: 8-Dimensional Scorecard Radar */}
          {activeTab === "radar" && (
            <div className="space-y-6">
              <div className="bg-[#111724]/90 border border-[#1e2738] rounded-xl p-5 shadow-xl">
                <div className="mb-6">
                  <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                    <Target className="w-4 h-4 text-indigo-400" />
                    8-Dimensional AI Evaluation Quality Framework
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Canonical evaluation dimensions per docs/Phases.md Section 26. Each dimension carries independent thresholds and audit trails.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {(Object.keys(DIMENSIONS_CONFIG) as CriterionType[]).map((dimKey) => {
                    const cfg = DIMENSIONS_CONFIG[dimKey];
                    const avgScore = telemetry?.avg_scores_by_criterion?.[dimKey] ?? (selectedRun ? selectedRun.criteria_scores.find(c => c.criterion === dimKey)?.score : 85);
                    const scoreVal = avgScore !== undefined ? Math.round(avgScore) : 85;

                    return (
                      <div
                        key={dimKey}
                        className={`p-4 rounded-xl border ${cfg.border} ${cfg.bg} flex flex-col justify-between transition hover:scale-[1.01]`}
                      >
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-lg">{cfg.icon}</span>
                            <span className="text-xs font-mono font-bold text-white bg-[#0c121e]/60 px-2 py-0.5 rounded border border-[#1e2738]">
                              {scoreVal}%
                            </span>
                          </div>
                          <h3 className="text-xs font-semibold text-white">{cfg.label}</h3>
                          <p className="text-[11px] text-slate-300 mt-1 leading-relaxed">
                            {cfg.description}
                          </p>
                        </div>

                        <div className="mt-4 pt-3 border-t border-slate-700/30">
                          <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                scoreVal >= 80 ? "bg-emerald-400" : scoreVal >= 60 ? "bg-amber-400" : "bg-rose-400"
                              }`}
                              style={{ width: `${scoreVal}%` }}
                            />
                          </div>
                          <div className="flex items-center justify-between text-[10px] text-slate-300 font-mono mt-1">
                            <span>Min Gate: 80%</span>
                            <span>{scoreVal >= 80 ? "VERIFIED" : "WARNING"}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: Representative Benchmark Suite */}
          {activeTab === "benchmarks" && (
            <div className="space-y-6">
              <div className="bg-[#111724]/90 border border-[#1e2738] rounded-xl p-5 shadow-xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                  <div>
                    <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-amber-400" />
                      Canonical Agent Benchmark Suite (Section 26)
                    </h2>
                    <p className="text-xs text-slate-400 mt-1">
                      Automated test suites across CEO, Marketing, Engineering, Sales, Tool, Approval, Failure, and Recovery scenarios.
                    </p>
                  </div>
                  <span className="text-xs font-mono text-slate-400">
                    {benchmarks.length} Standardized Benchmarks
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {benchmarks.map((bmk) => {
                    const col = CATEGORY_COLORS[bmk.category] || {
                      bg: "bg-slate-500/10",
                      text: "text-slate-400",
                      border: "border-slate-500/20",
                    };
                    const isRunning = runningBenchmarkId === bmk.id;

                    return (
                      <div
                        key={bmk.id}
                        className="p-4 rounded-xl bg-[#0d121c] border border-[#1e2738] hover:border-slate-700 transition flex flex-col justify-between"
                      >
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span
                              className={`text-[10px] font-mono px-2 py-0.5 rounded border ${col.bg} ${col.text} ${col.border}`}
                            >
                              {bmk.category}
                            </span>
                            <span className="text-[11px] font-mono text-slate-300">
                              Pass Gate: ≥ {bmk.passing_threshold}%
                            </span>
                          </div>

                          <h3 className="text-xs font-bold text-white mb-1">{bmk.name}</h3>
                          <p className="text-[11px] text-slate-400 leading-relaxed mb-3">
                            {bmk.description}
                          </p>

                          <div className="p-2.5 rounded-lg bg-[#080c14] border border-[#1a2232] font-mono text-[11px] text-slate-300 mb-3">
                            <span className="text-slate-300 select-none">$ prompt &gt; </span>
                            {bmk.canonical_prompt}
                          </div>
                        </div>

                        <div className="flex items-center justify-between pt-3 border-t border-[#1e2738]">
                          <div className="flex items-center gap-1.5">
                            {bmk.expected_criteria.slice(0, 3).map((crit) => (
                              <span
                                key={crit}
                                className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700"
                              >
                                {crit}
                              </span>
                            ))}
                            {bmk.expected_criteria.length > 3 && (
                              <span className="text-[9px] font-mono text-slate-300">
                                +{bmk.expected_criteria.length - 3}
                              </span>
                            )}
                          </div>

                          <button
                            onClick={() => handleExecuteBenchmark(bmk)}
                            disabled={isRunning}
                            className="px-3 py-1.5 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-amber-300 text-xs font-medium flex items-center gap-1.5 transition disabled:opacity-50"
                          >
                            {isRunning ? (
                              <>
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                Running...
                              </>
                            ) : (
                              <>
                                <Play className="w-3.5 h-3.5" />
                                Run Benchmark
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Benchmark Execution Result Banner */}
                {benchmarkResult && (
                  <div className="mt-6 p-4 rounded-xl bg-[#0e1626] border border-indigo-500/30 shadow-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {benchmarkResult.passed ? (
                          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        ) : (
                          <XCircle className="w-5 h-5 text-rose-400" />
                        )}
                        <h4 className="text-xs font-bold text-white">
                          Benchmark Result: {benchmarkResult.benchmark_name}
                        </h4>
                      </div>
                      <span className="text-xs font-mono font-bold text-emerald-400">
                        Score: {benchmarkResult.verification_run.overall_score} / 100
                      </span>
                    </div>
                    <p className="text-xs text-slate-300">
                      {benchmarkResult.verification_run.summary}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 4: Audit Log & Historical Runs */}
          {activeTab === "runs" && (
            <div className="space-y-6">
              <div className="bg-[#111724]/90 border border-[#1e2738] rounded-xl p-5 shadow-xl space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                      <Terminal className="w-4 h-4 text-cyan-400" />
                      Verification Audit Trail
                    </h2>
                    <p className="text-xs text-slate-400">
                      Historical log of all automated evaluations across tasks, artifacts, and benchmark suites.
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <Search className="w-3.5 h-3.5 text-slate-300 absolute left-2.5 top-2.5" />
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search ID, summary..."
                        className="bg-[#0d121c] border border-[#1e2738] text-xs text-white rounded-lg pl-8 pr-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500 w-48"
                      />
                    </div>

                    <select
                      aria-label="Filter Runs by Status"
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="bg-[#0d121c] border border-[#1e2738] text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="ALL">All Statuses</option>
                      <option value="PASSED">PASSED</option>
                      <option value="FAILED">FAILED</option>
                      <option value="RUNNING">RUNNING</option>
                    </select>
                  </div>
                </div>

                {/* Table */}
                <div className="border border-[#1e2738] rounded-lg overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[#0d121c] text-slate-300 font-mono text-[10px] uppercase border-b border-[#1e2738]">
                      <tr>
                        <th className="px-4 py-2.5">Status</th>
                        <th className="px-4 py-2.5">Target</th>
                        <th className="px-4 py-2.5">Score</th>
                        <th className="px-4 py-2.5">Stage</th>
                        <th className="px-4 py-2.5">Summary</th>
                        <th className="px-4 py-2.5">Timestamp</th>
                        <th className="px-4 py-2.5 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1e2738]">
                      {filteredRuns.length > 0 ? (
                        filteredRuns.map((r) => {
                          const isSelected = selectedRun?.id === r.id;
                          return (
                            <tr
                              key={r.id}
                              className={`hover:bg-slate-800/30 transition cursor-pointer ${
                                isSelected ? "bg-indigo-950/20" : ""
                              }`}
                              onClick={() => setSelectedRun(r)}
                            >
                              <td className="px-4 py-3">
                                <span
                                  className={`font-mono text-[10px] px-2 py-0.5 rounded-full border ${
                                    r.status === "PASSED"
                                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                                      : r.status === "FAILED"
                                      ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                                      : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                                  }`}
                                >
                                  {r.status}
                                </span>
                              </td>
                              <td className="px-4 py-3 font-mono text-slate-300">
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 mr-1.5">
                                  {r.target_type}
                                </span>
                                {r.target_id.slice(0, 16)}...
                              </td>
                              <td className="px-4 py-3 font-mono font-bold text-white">
                                {r.overall_score}
                              </td>
                              <td className="px-4 py-3 font-mono text-[11px] text-slate-400">
                                {r.pipeline_stage}
                              </td>
                              <td className="px-4 py-3 text-slate-300 max-w-xs truncate">
                                {r.summary || "—"}
                              </td>
                              <td className="px-4 py-3 font-mono text-[10px] text-slate-300 whitespace-nowrap">
                                {new Date(r.started_at).toLocaleString()}
                              </td>
                              <td className="px-4 py-3 text-right">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedRun(r);
                                    setActiveTab("pipeline");
                                  }}
                                  className="text-xs text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1"
                                >
                                  Inspect
                                  <ArrowRight className="w-3 h-3" />
                                </button>
                              </td>
                            </tr>
                          );
                        })
                      ) : (
                        <tr>
                          <td colSpan={7} className="px-4 py-8 text-center text-slate-300 text-xs">
                            No verification runs found matching current filter.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </ShellLayout>
  );
}
