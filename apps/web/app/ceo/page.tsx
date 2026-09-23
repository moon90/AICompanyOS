"use client";

import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Bot,
  Brain,
  Building2,
  CheckCircle2,
  Clock,
  Database,
  ExternalLink,
  FileText,
  FolderGit2,
  GitBranch,
  HelpCircle,
  History,
  Layers,
  ListTodo,
  Loader2,
  PlusCircle,
  RefreshCw,
  Send,
  Share2,
  Shield,
  ShieldAlert,
  Sparkles,
  Users,
} from "lucide-react";
import Link from "next/link";
import {
  api,
  CeoContext,
  CeoInquiryResponse,
  CeoPlanDetail,
  CeoPlanSummary,
  Company,
  CompanyDecision,
  CompanyStateResponse,
  CreatePlanPayload,
} from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

export default function CeoCommandCenterPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [activeCompany, setActiveCompany] = useState<Company | null>(null);
  const [context, setContext] = useState<CeoContext | null>(null);
  const [plans, setPlans] = useState<CeoPlanSummary[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<CeoPlanDetail | null>(null);
  const [activeTab, setActiveTab] = useState<"dag" | "delegation" | "governance">("dag");

  // Mode Switcher (Phase 5 Planning vs Phase 11 Grounded Memory & Knowledge Q&A)
  const [pageMode, setPageMode] = useState<"planning" | "memory">("planning");

  // Memory & Decisions State
  const [companyState, setCompanyState] = useState<CompanyStateResponse | null>(null);
  const [memoryLoading, setMemoryLoading] = useState(false);
  const [decisions, setDecisions] = useState<CompanyDecision[]>([]);
  const [decisionsFilter, setDecisionsFilter] = useState<"ALL" | "ACTIVE" | "SUPERSEDED">("ALL");
  const [inquiryQuestion, setInquiryQuestion] = useState("");
  const [inquiryLoading, setInquiryLoading] = useState(false);
  const [inquiryResult, setInquiryResult] = useState<CeoInquiryResponse | null>(null);
  const [showRecordModal, setShowRecordModal] = useState(false);
  const [supersedingTarget, setSupersedingTarget] = useState<CompanyDecision | null>(null);
  const [recordingDecision, setRecordingDecision] = useState(false);
  const [decisionTitle, setDecisionTitle] = useState("");
  const [decisionOutcome, setDecisionOutcome] = useState("");
  const [decisionRationale, setDecisionRationale] = useState("");
  const [decisionProjectId, setDecisionProjectId] = useState("");
  const [showRawState, setShowRawState] = useState(false);

  // Form State
  const [objective, setObjective] = useState("");
  const [requestedOutcome, setRequestedOutcome] = useState("");
  const [priority, setPriority] = useState<"low" | "medium" | "high" | "critical">("high");
  const [constraintsText, setConstraintsText] = useState("");
  const [requirementsText, setRequirementsText] = useState("");

  const [loading, setLoading] = useState(true);
  const [planning, setPlanning] = useState(false);
  const [planLoading, setPlanLoading] = useState(false);
  const [delegating, setDelegating] = useState(false);
  const [delegationSuccess, setDelegationSuccess] = useState<{
    project_id: string;
    project_name: string;
    parent_task_id: string;
    child_tasks_count: number;
    dependencies_count: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load Companies on Mount
  useEffect(() => {
    async function loadCompanies() {
      try {
        const comps = await api.getCompanies();
        setCompanies(comps);
        if (comps.length > 0) {
          setActiveCompany(comps[0]);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load company organizations");
      } finally {
        setLoading(false);
      }
    }
    loadCompanies();
  }, []);

  const loadPlanDetail = React.useCallback(async (planId: string, companyId?: string) => {
    const targetCompanyId = companyId || activeCompany?.id;
    if (!targetCompanyId) return;
    setPlanLoading(true);
    try {
      const detail = await api.getPlan(targetCompanyId, planId);
      setSelectedPlan(detail);
    } catch (err: any) {
      setError(err.message || "Failed to fetch plan detail");
    } finally {
      setPlanLoading(false);
    }
  }, [activeCompany?.id]);

  const loadMemoryData = React.useCallback(async (companyId?: string) => {
    const targetCompanyId = companyId || activeCompany?.id;
    if (!targetCompanyId) return;
    setMemoryLoading(true);
    try {
      const [stateRes, decsRes] = await Promise.all([
        api.getCompanyState(targetCompanyId).catch(() => null),
        api.getCompanyDecisions(targetCompanyId).catch(() => ({ items: [], total: 0 })),
      ]);
      setCompanyState(stateRes);
      setDecisions(decsRes.items);
    } catch (err: any) {
      setError(err.message || "Failed to load company memory state");
    } finally {
      setMemoryLoading(false);
    }
  }, [activeCompany?.id]);

  // Load Context and Plans when Active Company changes
  useEffect(() => {
    if (!activeCompany) return;
    async function loadData() {
      setError(null);
      try {
        const [ctx, plns] = await Promise.all([
          api.getCeoContext(activeCompany!.id).catch(() => null),
          api.getPlans(activeCompany!.id).catch(() => []),
        ]);
        setContext(ctx);
        setPlans(plns);
        if (plns.length > 0) {
          loadPlanDetail(plns[0].id, activeCompany!.id);
        } else {
          setSelectedPlan(null);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load CEO context");
      }
    }
    loadData();
    if (pageMode === "memory") {
      loadMemoryData(activeCompany.id);
    }
  }, [activeCompany, loadPlanDetail, loadMemoryData, pageMode]);

  async function handleCreatePlan(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompany || !objective.trim()) return;

    setPlanning(true);
    setError(null);

    const constraints = constraintsText
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);
    const requirements = requirementsText
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);

    const payload: CreatePlanPayload = {
      objective: objective.trim(),
      requested_outcome: requestedOutcome.trim() || undefined,
      priority,
      constraints,
      requirements,
    };

    try {
      const plan = await api.createPlan(activeCompany.id, payload);
      setSelectedPlan(plan);
      // Refresh list
      const plns = await api.getPlans(activeCompany.id);
      setPlans(plns);
      // Reset form
      setObjective("");
      setRequestedOutcome("");
      setConstraintsText("");
      setRequirementsText("");
    } catch (err: any) {
      setError(err.message || "Failed to generate structured plan");
    } finally {
      setPlanning(false);
    }
  }

  async function handleDelegatePlan() {
    if (!activeCompany || !selectedPlan) return;
    setDelegating(true);
    setError(null);
    setDelegationSuccess(null);

    try {
      const result = await api.delegatePlan(activeCompany.id, selectedPlan.id);
      setDelegationSuccess({
        project_id: result.project_id,
        project_name: result.project_name,
        parent_task_id: result.parent_task_id,
        child_tasks_count: result.child_tasks_count,
        dependencies_count: result.dependencies_count,
      });
      // Refresh plan detail to show delegated status
      await loadPlanDetail(selectedPlan.id);
    } catch (err: any) {
      setError(err.message || "Failed to delegate plan into active work hierarchy");
    } finally {
      setDelegating(false);
    }
  }

  async function handleAskCeo(questionToAsk?: string) {
    const q = (questionToAsk || inquiryQuestion).trim();
    if (!activeCompany || !q) return;

    setInquiryLoading(true);
    setError(null);
    try {
      const res = await api.inquireCeo(activeCompany.id, q);
      setInquiryResult(res);
      setInquiryQuestion("");
    } catch (err: any) {
      setError(err.message || "Failed to process CEO inquiry");
    } finally {
      setInquiryLoading(false);
    }
  }

  async function handleSubmitDecision(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompany || !decisionTitle.trim() || !decisionOutcome.trim() || !decisionRationale.trim()) {
      return;
    }

    setRecordingDecision(true);
    setError(null);
    try {
      const payload = {
        title: decisionTitle.trim(),
        decision: decisionOutcome.trim(),
        rationale: decisionRationale.trim(),
        project_id: decisionProjectId.trim() || undefined,
      };

      if (supersedingTarget) {
        await api.supersedeCompanyDecision(activeCompany.id, supersedingTarget.id, payload);
      } else {
        await api.createCompanyDecision(activeCompany.id, payload);
      }

      setShowRecordModal(false);
      setSupersedingTarget(null);
      setDecisionTitle("");
      setDecisionOutcome("");
      setDecisionRationale("");
      setDecisionProjectId("");
      await loadMemoryData(activeCompany.id);
    } catch (err: any) {
      setError(err.message || "Failed to record company decision");
    } finally {
      setRecordingDecision(false);
    }
  }

  function openSupersedeModal(decision: CompanyDecision) {
    setSupersedingTarget(decision);
    setDecisionTitle(`Revised: ${decision.title}`);
    setDecisionOutcome("");
    setDecisionRationale(`Supersedes ${decision.title} due to: `);
    setDecisionProjectId(decision.project_id || "");
    setShowRecordModal(true);
  }

  if (loading) {
    return (
      <ShellLayout pageTitle="CEO Orchestrator" breadcrumb="Executive Command Center">
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      </ShellLayout>
    );
  }

  if (companies.length === 0) {
    return (
      <ShellLayout pageTitle="CEO Orchestrator" breadcrumb="Executive Command Center">
        <div className="p-8 border border-border rounded-xl bg-surface-card text-center max-w-xl mx-auto mt-12">
          <Building2 className="w-12 h-12 text-primary mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-text-primary mb-2">
            No Organization Found
          </h2>
          <p className="text-text-secondary text-sm mb-6">
            An active company organization is required before accessing the CEO Command Center.
          </p>
          <Link
            href="/company"
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-black font-medium text-sm rounded-lg hover:bg-primary/90 transition-colors"
          >
            Create Company Organization
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </ShellLayout>
    );
  }

  const ceo = context?.ceo_agent;
  const filteredDecisions = decisions.filter((d) => {
    if (decisionsFilter === "ALL") return true;
    return d.status === decisionsFilter;
  });

  return (
    <ShellLayout pageTitle="CEO Orchestrator" breadcrumb="Executive Command Center">
      <div className="space-y-6 max-w-7xl mx-auto">
        {/* Company Selector & Strategic Strip */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-surface-elevated border border-border p-4 rounded-xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-semibold text-text-primary">
                  {context?.company.name || activeCompany?.name}
                </h1>
                <span className="px-2 py-0.5 text-xs rounded bg-surface-card text-text-secondary border border-border">
                  {context?.company.industry || "General Industry"}
                </span>
              </div>
              <p className="text-xs text-text-muted mt-0.5 line-clamp-1">
                {context?.company.mission || "Autonomous AI Company Operations"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="text-right">
              <span className="text-text-muted">Org Structure:</span>{" "}
              <span className="text-text-primary font-medium">
                {context?.department_count || 0} Depts · {context?.agent_count || 0} Agents
              </span>
            </div>
            {companies.length > 1 && (
              <select
                value={activeCompany?.id}
                onChange={(e) => {
                  const comp = companies.find((c) => c.id === e.target.value);
                  if (comp) setActiveCompany(comp);
                }}
                className="bg-surface-card border border-border text-text-primary rounded-lg px-2.5 py-1 text-xs focus:outline-none focus:border-primary"
              >
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* CEO Identity Status / Missing CEO Alert */}
        {!ceo ? (
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-semibold text-amber-300">
                  No CEO Agent Registered
                </h3>
                <p className="text-xs text-text-secondary mt-1">
                  The CEO Command Center requires a registered CEO agent to intake goals and formulate structured plan proposals.
                </p>
              </div>
            </div>
            <Link
              href="/agents"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-500 text-black font-medium text-xs rounded-lg hover:bg-amber-400 transition-colors shrink-0"
            >
              Provision in Agent Registry
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        ) : (
          <div className="p-3.5 rounded-xl bg-surface-card border border-border flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center font-bold text-xs">
                CEO
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-text-primary">
                    {ceo.name}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-surface border border-border text-text-muted">
                    ID: {ceo.id.slice(0, 8)}...
                  </span>
                </div>
                <p className="text-[11px] text-text-muted">
                  Executive Authority: <strong className="text-text-secondary">Orchestration & State Grounding</strong>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 text-xs text-text-muted">
              <span className="flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                Registry Active
              </span>
              <span>·</span>
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-text-muted" />
                0 Runtime Active (Phase 14)
              </span>
            </div>
          </div>
        )}

        {/* Global Error Alert */}
        {error && (
          <div className="p-3.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Executive Mode Switcher (Phase 5 Planning vs Phase 11 Grounded Memory & Knowledge Q&A) */}
        <div className="flex items-center justify-between gap-3 p-1.5 bg-surface-elevated border border-border rounded-xl">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPageMode("planning")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                pageMode === "planning"
                  ? "bg-primary text-white shadow-sm"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              <GitBranch className="w-3.5 h-3.5" />
              Executive Planning & Delegation
            </button>
            <button
              onClick={() => {
                setPageMode("memory");
                loadMemoryData();
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                pageMode === "memory"
                  ? "bg-primary text-white shadow-sm"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              <Brain className="w-3.5 h-3.5" />
              Company State Memory & Grounded Q&A
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Phase 11
              </span>
            </button>
          </div>

          {pageMode === "memory" && (
            <button
              onClick={() => loadMemoryData()}
              disabled={memoryLoading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface border border-border text-xs text-text-secondary hover:text-text-primary hover:border-text-muted transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${memoryLoading ? "animate-spin" : ""}`} />
              Refresh Snapshot
            </button>
          )}
        </div>

        {/* ========================================================================= */}
        {/* PHASE 11 WORKSPACE: Grounded Memory, Company State & CEO Q&A */}
        {/* ========================================================================= */}
        {pageMode === "memory" ? (
          <div className="space-y-6">
            {/* Grounded CEO Q&A Inquiry Box */}
            <div className="p-6 rounded-xl bg-surface-card border border-border space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-border">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    <Brain className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                      Grounded CEO Knowledge & Operational Q&A
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        Strict Zero Hallucination (docs/Phases.md § 15)
                      </span>
                    </h2>
                    <p className="text-xs text-text-secondary mt-0.5">
                      The CEO answers operational questions grounded exclusively in persistent PostgreSQL state without inventing information.
                    </p>
                  </div>
                </div>
              </div>

              {/* Inquiry Input Bar */}
              <div className="space-y-3">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleAskCeo();
                  }}
                  className="flex items-center gap-2"
                >
                  <input
                    type="text"
                    value={inquiryQuestion}
                    onChange={(e) => setInquiryQuestion(e.target.value)}
                    placeholder="Ask the CEO about company mission, active decisions, projects, tasks, team..."
                    className="flex-1 bg-surface border border-border text-text-primary rounded-lg px-4 py-2.5 text-xs focus:outline-none focus:border-primary transition"
                  />
                  <button
                    type="submit"
                    disabled={inquiryLoading || !inquiryQuestion.trim()}
                    className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-sm transition disabled:opacity-50"
                  >
                    {inquiryLoading ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        Inquiring CEO...
                      </>
                    ) : (
                      <>
                        <Send className="w-3.5 h-3.5" />
                        Ask CEO
                      </>
                    )}
                  </button>
                </form>

                {/* Quick Prompt Chips */}
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="text-text-muted text-[11px] font-medium">Quick Prompts:</span>
                  {[
                    "What is our company mission?",
                    "What decisions have been made?",
                    "Which decisions were superseded?",
                    "What projects are currently active?",
                    "Who is on our agent roster?",
                    "What is the status of our task pipeline?",
                    "Do we have any pending approvals?",
                  ].map((chip) => (
                    <button
                      key={chip}
                      type="button"
                      onClick={() => handleAskCeo(chip)}
                      disabled={inquiryLoading}
                      className="px-2.5 py-1 rounded-md bg-surface hover:bg-surface-elevated border border-border/80 text-[11px] text-text-secondary hover:text-text-primary transition"
                    >
                      {chip}
                    </button>
                  ))}
                </div>
              </div>

              {/* Inquiry Result Card */}
              {inquiryResult && (
                <div className="mt-4 p-4 rounded-xl bg-surface-elevated border border-primary/30 space-y-3">
                  <div className="flex items-center justify-between text-xs pb-2 border-b border-border/60">
                    <div className="flex items-center gap-2 text-primary font-semibold">
                      <Bot className="w-4 h-4" />
                      <span>Authoritative CEO Response</span>
                    </div>
                    <span className="text-[11px] text-text-muted font-mono">
                      Grounded State Snapshot: {new Date(inquiryResult.grounded_state_timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <div className="text-xs text-text-primary leading-relaxed whitespace-pre-wrap font-sans">
                    {inquiryResult.answer}
                  </div>

                  {/* Citations */}
                  {inquiryResult.citations.length > 0 && (
                    <div className="pt-2 border-t border-border/60 space-y-1.5">
                      <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
                        Authoritative Sources Cited:
                      </span>
                      <div className="flex flex-wrap gap-2">
                        {inquiryResult.citations.map((cite, idx) => (
                          <div
                            key={idx}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface border border-border text-[11px]"
                          >
                            <span className="font-mono font-semibold text-indigo-400 text-[10px]">
                              [{cite.source_type}]
                            </span>
                            <span className="text-text-secondary">{cite.reference}</span>
                            <span className="text-text-muted font-mono text-[9px]">
                              ({cite.source_id.slice(0, 8)}...)
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Operational State Telemetry Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="p-3.5 rounded-xl bg-surface-card border border-border space-y-1">
                <span className="text-[11px] text-text-muted font-medium">Organization</span>
                <p className="text-sm font-bold text-text-primary truncate">
                  {companyState?.company.name || activeCompany?.name}
                </p>
                <span className="text-[10px] text-emerald-400 font-mono">ID Verified</span>
              </div>
              <div className="p-3.5 rounded-xl bg-surface-card border border-border space-y-1">
                <span className="text-[11px] text-text-muted font-medium">Departments</span>
                <p className="text-sm font-bold text-text-primary">
                  {companyState?.departments.length || 0} Active
                </p>
                <span className="text-[10px] text-text-muted font-mono">Structural divisions</span>
              </div>
              <div className="p-3.5 rounded-xl bg-surface-card border border-border space-y-1">
                <span className="text-[11px] text-text-muted font-medium">Registered Agents</span>
                <p className="text-sm font-bold text-text-primary">
                  {companyState?.agents.length || 0} Registered
                </p>
                <span className="text-[10px] text-text-muted font-mono">0 active (Phase 14)</span>
              </div>
              <div className="p-3.5 rounded-xl bg-surface-card border border-border space-y-1">
                <span className="text-[11px] text-text-muted font-medium">Projects</span>
                <p className="text-sm font-bold text-text-primary">
                  {companyState?.projects.length || 0} Recorded
                </p>
                <span className="text-[10px] text-text-muted font-mono">Active & Planned</span>
              </div>
              <div className="p-3.5 rounded-xl bg-surface-card border border-border space-y-1">
                <span className="text-[11px] text-text-muted font-medium">Task Pipeline</span>
                <p className="text-sm font-bold text-text-primary">
                  {companyState?.tasks_summary.total || 0} Tasks
                </p>
                <span className="text-[10px] text-text-muted font-mono">
                  {Object.keys(companyState?.tasks_summary.by_status || {}).length} statuses
                </span>
              </div>
              <div className="p-3.5 rounded-xl bg-surface-card border border-border space-y-1">
                <span className="text-[11px] text-text-muted font-medium">Decisions Chain</span>
                <p className="text-sm font-bold text-indigo-400">
                  {decisions.length} Decisions
                </p>
                <span className="text-[10px] text-text-muted font-mono">Immutable audit trail</span>
              </div>
            </div>

            {/* Authoritative Company Decisions Registry */}
            <div className="p-6 rounded-xl bg-surface-card border border-border space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-primary/10 text-primary border border-primary/20">
                    <Database className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                      Authoritative Company Decisions & Policies (docs/Memory.md § 33)
                    </h3>
                    <p className="text-xs text-text-secondary mt-0.5">
                      Durable architectural and strategic determinations. Decisions are immutable; revisions supersede past records.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex items-center bg-surface border border-border rounded-lg p-0.5 text-xs">
                    {(["ALL", "ACTIVE", "SUPERSEDED"] as const).map((filter) => (
                      <button
                        key={filter}
                        onClick={() => setDecisionsFilter(filter)}
                        className={`px-3 py-1 rounded-md transition font-medium ${
                          decisionsFilter === filter
                            ? "bg-primary text-white"
                            : "text-text-muted hover:text-text-secondary"
                        }`}
                      >
                        {filter}
                      </button>
                    ))}
                  </div>

                  <button
                    onClick={() => {
                      setSupersedingTarget(null);
                      setDecisionTitle("");
                      setDecisionOutcome("");
                      setDecisionRationale("");
                      setDecisionProjectId("");
                      setShowRecordModal(true);
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-sm transition"
                  >
                    <PlusCircle className="w-3.5 h-3.5" />
                    Record Decision
                  </button>
                </div>
              </div>

              {/* Decisions List */}
              {filteredDecisions.length === 0 ? (
                <div className="p-8 text-center text-xs text-text-muted border border-dashed border-border rounded-xl">
                  <Database className="w-8 h-8 text-text-muted mx-auto mb-2 opacity-50" />
                  No decisions match filter &apos;{decisionsFilter}&apos;. Record a new decision above.
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredDecisions.map((dec) => (
                    <div
                      key={dec.id}
                      className="p-4 rounded-xl bg-surface border border-border space-y-2 hover:border-text-muted/50 transition"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-xs text-text-primary">
                              {dec.title}
                            </span>
                            <span
                              className={`text-[10px] font-mono px-2 py-0.5 rounded-full uppercase tracking-wider ${
                                dec.status === "ACTIVE"
                                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                  : dec.status === "SUPERSEDED"
                                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                  : "bg-slate-500/10 text-slate-400 border border-slate-500/20"
                              }`}
                            >
                              {dec.status}
                            </span>
                          </div>
                          <p className="text-xs text-text-secondary leading-relaxed">
                            <strong className="text-text-primary">Determination:</strong> {dec.decision}
                          </p>
                          <p className="text-[11px] text-text-muted leading-relaxed font-mono">
                            Rationale: {dec.rationale}
                          </p>
                        </div>

                        {dec.status === "ACTIVE" && (
                          <button
                            onClick={() => openSupersedeModal(dec)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[11px] font-medium transition shrink-0"
                          >
                            <Share2 className="w-3 h-3" />
                            Supersede
                          </button>
                        )}
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-text-muted pt-2 border-t border-border/50 font-mono">
                        <div className="flex items-center gap-3">
                          <span>Decision ID: {dec.id.slice(0, 8)}...</span>
                          {dec.superseded_by_decision_id && (
                            <span className="text-amber-400">
                              Superseded by: {dec.superseded_by_decision_id.slice(0, 8)}...
                            </span>
                          )}
                        </div>
                        <span>{new Date(dec.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Toggle Raw State Inspector */}
            <div className="p-4 rounded-xl bg-surface-card border border-border space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold text-text-primary">
                  <FileText className="w-4 h-4 text-text-secondary" />
                  <span>Authoritative Operational State Packet (Context Payload)</span>
                </div>
                <button
                  onClick={() => setShowRawState(!showRawState)}
                  className="text-xs text-primary hover:underline font-medium"
                >
                  {showRawState ? "Hide Raw State Packet" : "View Raw State Packet"}
                </button>
              </div>

              {showRawState && companyState && (
                <pre className="p-4 rounded-lg bg-surface border border-border text-[11px] font-mono text-text-secondary overflow-x-auto max-h-[350px]">
                  {JSON.stringify(companyState, null, 2)}
                </pre>
              )}
            </div>
          </div>
        ) : (
          /* ========================================================================= */
          /* PHASE 5 WORKSPACE: Executive Planning & Delegation */
          /* ========================================================================= */
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Goal Intake & Plan History (5 cols) */}
            <div className="lg:col-span-5 space-y-6">
              {/* CEO Command Box */}
              <div className="p-5 rounded-xl bg-surface-card border border-border space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-primary" />
                    <h2 className="text-sm font-semibold text-text-primary">
                      Executive Goal Intake
                    </h2>
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-surface border border-border text-text-muted">
                    Phase 5 Active
                  </span>
                </div>
                <p className="text-xs text-text-secondary leading-relaxed">
                  Provide high-level strategic objectives. The CEO agent will formulate a structured DAG plan proposal with departmental workstreams.
                </p>

                <form onSubmit={handleCreatePlan} className="space-y-3.5">
                  <div>
                    <label className="block text-xs font-medium text-text-secondary mb-1">
                      Objective Goal <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={objective}
                      onChange={(e) => setObjective(e.target.value)}
                      placeholder="e.g. Build an autonomous marketing funnel for Q3"
                      className="w-full bg-surface border border-border text-text-primary rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-primary"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-text-secondary mb-1">
                      Requested Outcome
                    </label>
                    <input
                      type="text"
                      value={requestedOutcome}
                      onChange={(e) => setRequestedOutcome(e.target.value)}
                      placeholder="e.g. 5,000 qualified enterprise leads generated"
                      className="w-full bg-surface border border-border text-text-primary rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-primary"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-text-secondary mb-1">
                      Priority Level
                    </label>
                    <select
                      value={priority}
                      onChange={(e: any) => setPriority(e.target.value)}
                      className="w-full bg-surface border border-border text-text-primary rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-primary"
                    >
                      <option value="low">Low Priority</option>
                      <option value="medium">Medium Priority</option>
                      <option value="high">High Priority</option>
                      <option value="critical">Critical Priority</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-text-secondary mb-1">
                      Constraints (one per line)
                    </label>
                    <textarea
                      rows={2}
                      value={constraintsText}
                      onChange={(e) => setConstraintsText(e.target.value)}
                      placeholder="e.g. Budget under $10,000&#10;No external tracking cookies"
                      className="w-full bg-surface border border-border text-text-primary rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-primary"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-text-secondary mb-1">
                      Requirements (one per line)
                    </label>
                    <textarea
                      rows={2}
                      value={requirementsText}
                      onChange={(e) => setRequirementsText(e.target.value)}
                      placeholder="e.g. Integrate with HubSpot API&#10;Require human review before publishing"
                      className="w-full bg-surface border border-border text-text-primary rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-primary"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={planning || !ceo}
                    className="w-full py-2.5 px-4 bg-primary hover:bg-primary-hover text-white rounded-lg text-xs font-semibold shadow-sm transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {planning ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        Formulating Structured Plan...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5" />
                        Synthesize Executive Plan
                      </>
                    )}
                  </button>
                </form>
              </div>

              {/* Proposals History */}
              <div className="p-4 rounded-xl bg-surface-card border border-border space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-text-primary">
                    <History className="w-4 h-4 text-text-secondary" />
                    <h3 className="text-sm font-semibold">Plan Proposals History</h3>
                  </div>
                  <span className="text-xs text-text-muted font-mono">
                    {plans.length} total
                  </span>
                </div>

                {plans.length === 0 ? (
                  <p className="text-xs text-text-muted text-center py-6">
                    No plans synthesized yet. Submit an executive objective above.
                  </p>
                ) : (
                  <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
                    {plans.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => loadPlanDetail(p.id)}
                        className={`w-full text-left p-3 rounded-lg border transition-all text-xs space-y-1.5 ${
                          selectedPlan?.id === p.id
                            ? "bg-primary/10 border-primary/40 text-text-primary"
                            : "bg-surface border-border text-text-secondary hover:border-text-muted"
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium text-text-primary truncate">
                            {p.goal}
                          </span>
                          <span
                            className={`text-[10px] px-1.5 py-0.5 rounded font-medium shrink-0 uppercase tracking-wider ${
                              p.priority === "critical"
                                ? "bg-red-500/20 text-red-400 border border-red-500/30"
                                : p.priority === "high"
                                ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                                : "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                            }`}
                          >
                            {p.priority}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-[11px] text-text-muted">
                          <span>{p.step_count} DAG Steps</span>
                          <span>{new Date(p.created_at).toLocaleDateString()}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Right Column: Selected Plan Breakdown (7 cols) */}
            <div className="lg:col-span-7">
              {planLoading ? (
                <div className="p-12 border border-border rounded-xl bg-surface-card flex items-center justify-center min-h-[400px]">
                  <Loader2 className="w-8 h-8 text-primary animate-spin" />
                </div>
              ) : !selectedPlan ? (
                <div className="p-12 border border-border rounded-xl bg-surface-card text-center flex flex-col items-center justify-center min-h-[400px]">
                  <Layers className="w-12 h-12 text-text-muted mb-3" />
                  <h3 className="text-base font-semibold text-text-primary">
                    No Plan Selected
                  </h3>
                  <p className="text-xs text-text-muted max-w-sm mt-1">
                    Submit a goal above or select an existing proposal to view its task graph DAG, delegation breakdown, and approval requirements.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Strict Boundary Callout */}
                  <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-300 flex items-start gap-2.5">
                    <Shield className="w-4 h-4 shrink-0 mt-0.5 text-indigo-400" />
                    <div>
                      <span className="font-semibold text-indigo-200">Execution Phase Boundary:</span>{" "}
                      This DAG proposal decomposes goals into validated departments and dependencies. Actual agent execution loops activate in <strong className="text-indigo-100">Phase 8</strong>.
                    </div>
                  </div>

                  {/* Plan Header Card */}
                  <div className="p-5 rounded-xl bg-surface-card border border-border space-y-4">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <h2 className="text-base font-semibold text-text-primary">
                            {selectedPlan.goal}
                          </h2>
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded font-medium uppercase tracking-wider ${
                              selectedPlan.priority === "critical"
                                ? "bg-red-500/20 text-red-400 border border-red-500/30"
                                : selectedPlan.priority === "high"
                                ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                                : "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                            }`}
                          >
                            {selectedPlan.priority}
                          </span>
                        </div>
                        <p className="text-xs text-text-muted mt-1">
                          Generated {new Date(selectedPlan.created_at).toLocaleString()} by CEO Agent {selectedPlan.ceo_agent_id ? `${selectedPlan.ceo_agent_id.slice(0, 8)}...` : "System"}
                        </p>
                      </div>

                      {/* Delegation Button */}
                      <div>
                        {selectedPlan.status === "DELEGATED" ? (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Delegated
                          </span>
                        ) : (
                          <button
                            onClick={handleDelegatePlan}
                            disabled={delegating}
                            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-medium shadow-sm transition disabled:opacity-50"
                          >
                            {delegating ? (
                              <>
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                Decomposing & Delegating...
                              </>
                            ) : (
                              <>
                                <Share2 className="w-3.5 h-3.5" />
                                Delegate & Launch Workflows
                              </>
                            )}
                          </button>
                        )}
                      </div>
                    </div>

                    {delegationSuccess && (
                      <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 space-y-2">
                        <div className="flex items-center gap-2 font-medium">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                          <span>Plan successfully decomposed and delegated!</span>
                        </div>
                        <p className="text-emerald-400/90 text-[11px]">
                          Created Project &quot;{delegationSuccess.project_name}&quot; with 1 parent task, {delegationSuccess.child_tasks_count} child workstreams, and {delegationSuccess.dependencies_count} prerequisite dependencies.
                        </p>
                        <div className="flex items-center gap-3 pt-1">
                          <Link
                            href="/projects"
                            className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-300 hover:text-white underline"
                          >
                            <FolderGit2 className="w-3 h-3" />
                            View in Projects
                          </Link>
                          <Link
                            href="/tasks"
                            className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-300 hover:text-white underline"
                          >
                            <ListTodo className="w-3 h-3" />
                            View in Tasks Console
                          </Link>
                        </div>
                      </div>
                    )}

                    {selectedPlan.requested_outcome && (
                      <div className="text-xs text-text-secondary bg-surface p-2.5 rounded-lg border border-border">
                        <span className="text-text-muted font-medium">Desired Outcome:</span>{" "}
                        {selectedPlan.requested_outcome}
                      </div>
                    )}

                    {/* Audit-Safe Reasoning Summary */}
                    <div className="text-xs space-y-1">
                      <span className="text-text-muted font-medium">CEO Reasoning Summary:</span>
                      <p className="text-text-secondary bg-surface-elevated p-3 rounded-lg border border-border/80 leading-relaxed font-mono text-[11px]">
                        {selectedPlan.reasoning_summary}
                      </p>
                    </div>
                  </div>

                  {/* Navigation Tabs */}
                  <div className="flex items-center border-b border-border text-xs gap-1">
                    <button
                      onClick={() => setActiveTab("dag")}
                      className={`flex items-center gap-2 px-4 py-2.5 font-medium border-b-2 transition-colors ${
                        activeTab === "dag"
                          ? "border-primary text-text-primary"
                          : "border-transparent text-text-muted hover:text-text-secondary"
                      }`}
                    >
                      <GitBranch className="w-3.5 h-3.5" />
                      Task Graph DAG ({selectedPlan.plan_steps.length})
                    </button>
                    <button
                      onClick={() => setActiveTab("delegation")}
                      className={`flex items-center gap-2 px-4 py-2.5 font-medium border-b-2 transition-colors ${
                        activeTab === "delegation"
                          ? "border-primary text-text-primary"
                          : "border-transparent text-text-muted hover:text-text-secondary"
                      }`}
                    >
                      <Users className="w-3.5 h-3.5" />
                      Department Delegations ({selectedPlan.delegation_proposals.length})
                    </button>
                    <button
                      onClick={() => setActiveTab("governance")}
                      className={`flex items-center gap-2 px-4 py-2.5 font-medium border-b-2 transition-colors ${
                        activeTab === "governance"
                          ? "border-primary text-text-primary"
                          : "border-transparent text-text-muted hover:text-text-secondary"
                      }`}
                    >
                      <ShieldAlert className="w-3.5 h-3.5" />
                      Approvals & Governance ({selectedPlan.approval_requirements.length})
                    </button>
                  </div>

                  {/* Tab 1: DAG Graph View */}
                  {activeTab === "dag" && (
                    <div className="space-y-3">
                      {selectedPlan.plan_steps.map((step, idx) => (
                        <div
                          key={step.step_id}
                          className="p-4 rounded-xl bg-surface-card border border-border space-y-2 hover:border-text-muted/50 transition-colors"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex items-center gap-2.5">
                              <span className="w-6 h-6 rounded-md bg-surface flex items-center justify-center font-mono text-[11px] font-semibold text-text-primary border border-border">
                                {idx + 1}
                              </span>
                              <div>
                                <h4 className="text-xs font-semibold text-text-primary">
                                  {step.title}
                                </h4>
                                <span className="text-[10px] font-mono text-text-muted">
                                  ID: {step.step_id}
                                </span>
                              </div>
                            </div>

                            <div className="flex items-center gap-1.5">
                              {step.assigned_agent_role && (
                                <span className="text-[10px] px-2 py-0.5 rounded bg-primary/10 border border-primary/20 text-primary font-medium">
                                  {step.assigned_agent_role}
                                </span>
                              )}
                              <span className="text-[10px] px-2 py-0.5 rounded bg-surface border border-border text-text-secondary font-medium">
                                Dept: {step.department_code ?? "General"}
                              </span>
                            </div>
                          </div>

                          <p className="text-xs text-text-secondary leading-relaxed pl-8.5">
                            {step.description}
                          </p>

                          {/* Prerequisites / Dependencies */}
                          {step.depends_on && step.depends_on.length > 0 && (
                            <div className="pl-8.5 pt-1 flex items-center gap-2 text-[11px] text-text-muted">
                              <GitBranch className="w-3 h-3 text-text-muted shrink-0" />
                              <span>Depends on:</span>
                              <div className="flex flex-wrap gap-1">
                                {step.depends_on.map((dep) => (
                                  <span
                                    key={dep}
                                    className="font-mono text-[10px] px-1.5 py-0.2 rounded bg-surface border border-border text-text-secondary"
                                  >
                                    {dep}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 2: Department Delegations View */}
                  {activeTab === "delegation" && (
                    <div className="space-y-3">
                      {selectedPlan.delegation_proposals.map((del, idx) => (
                        <div
                          key={idx}
                          className="p-4 rounded-xl bg-surface-card border border-border space-y-2.5"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Users className="w-4 h-4 text-primary" />
                              <h4 className="text-xs font-semibold text-text-primary">
                                Role: {del.target_role}
                              </h4>
                            </div>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface border border-border text-text-muted">
                              Auth Level {del.authority_level_required}
                            </span>
                          </div>

                          <div className="text-xs text-text-secondary bg-surface p-3 rounded-lg border border-border/80">
                            <span className="text-text-muted font-medium">Objective:</span>{" "}
                            {del.objective}
                          </div>

                          <div className="text-xs text-text-secondary bg-surface p-3 rounded-lg border border-border/80">
                            <span className="text-text-muted font-medium">Scope:</span>{" "}
                            {del.scope}
                          </div>

                          {del.required_capabilities && del.required_capabilities.length > 0 && (
                            <div className="flex items-center gap-1.5 text-[11px] text-text-muted">
                              <span>Required Capabilities:</span>
                              <div className="flex flex-wrap gap-1">
                                {del.required_capabilities.map((cap) => (
                                  <span
                                    key={cap}
                                    className="font-mono text-[10px] px-1.5 py-0.2 rounded bg-surface border border-border text-text-secondary"
                                  >
                                    {cap}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 3: Governance & Approvals View */}
                  {activeTab === "governance" && (
                    <div className="space-y-4">
                      {/* Human Approval Gates */}
                      <div className="p-4 rounded-xl bg-surface-card border border-border space-y-3">
                        <div className="flex items-center gap-2 text-text-primary">
                          <ShieldAlert className="w-4 h-4 text-amber-400" />
                          <h4 className="text-xs font-semibold">Human Approval Requirements</h4>
                        </div>

                        {selectedPlan.approval_requirements.length === 0 ? (
                          <p className="text-xs text-text-muted">
                            No high-consequence approval gates flagged for this plan proposal.
                          </p>
                        ) : (
                          <div className="space-y-2">
                            {selectedPlan.approval_requirements.map((gate, idx) => (
                              <div
                                key={idx}
                                className="p-3 rounded-lg bg-surface border border-border text-xs space-y-1"
                              >
                                <div className="flex items-center justify-between">
                                  <span className="font-semibold text-text-primary">
                                    Step: {gate.step_id}
                                  </span>
                                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase">
                                    Risk: {gate.risk_level}
                                  </span>
                                </div>
                                <p className="text-text-secondary text-[11px]">
                                  {gate.action_description}
                                </p>
                                <p className="text-text-muted text-[10px]">
                                  Reason: {gate.reason_for_approval}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Risk Assessment */}
                      <div className="p-4 rounded-xl bg-surface-card border border-border space-y-3">
                        <div className="flex items-center gap-2 text-text-primary">
                          <AlertTriangle className="w-4 h-4 text-primary" />
                          <h4 className="text-xs font-semibold">Risk Assessments & Mitigations</h4>
                        </div>

                        <div className="space-y-2">
                          {selectedPlan.risks.map((r, idx) => (
                            <div
                              key={idx}
                              className="p-3 rounded-lg bg-surface border border-border text-xs space-y-1"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-medium text-text-primary">
                                  Risk: {r.risk}
                                </span>
                                <span
                                  className={`text-[10px] px-1.5 py-0.2 rounded font-medium uppercase ${
                                    r.severity === "high" || r.severity === "critical"
                                      ? "text-red-400 bg-red-500/10 border border-red-500/20"
                                      : "text-amber-400 bg-amber-500/10 border border-amber-500/20"
                                  }`}
                                >
                                  {r.severity ?? "medium"}
                                </span>
                              </div>
                              <div className="text-text-muted">
                                Mitigation: <span className="text-text-secondary">{r.mitigation}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Assumptions */}
                      {selectedPlan.assumptions.length > 0 && (
                        <div className="p-4 rounded-xl bg-surface-card border border-border space-y-2">
                          <h4 className="font-semibold text-text-primary">Planning Assumptions</h4>
                          <ul className="list-disc list-inside text-text-secondary text-[11px] space-y-1">
                            {selectedPlan.assumptions.map((ass, idx) => (
                              <li key={idx}>{ass}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Modal: Record / Supersede Decision */}
        {showRecordModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-surface-elevated border border-border rounded-xl max-w-lg w-full p-6 space-y-4 shadow-xl">
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <div className="flex items-center gap-2">
                  <Database className="w-5 h-5 text-primary" />
                  <h3 className="text-sm font-semibold text-text-primary">
                    {supersedingTarget ? "Supersede Existing Decision" : "Record Authoritative Decision"}
                  </h3>
                </div>
                <button
                  onClick={() => {
                    setShowRecordModal(false);
                    setSupersedingTarget(null);
                  }}
                  className="text-text-muted hover:text-text-primary text-xs"
                >
                  ✕
                </button>
              </div>

              {supersedingTarget && (
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
                  <span>Superseding: </span>
                  <strong className="text-white">{supersedingTarget.title}</strong>
                  <p className="text-[11px] text-amber-400/80 mt-1">
                    The previous decision will be immutably preserved with status SUPERSEDED and point to this new decision.
                  </p>
                </div>
              )}

              <form onSubmit={handleSubmitDecision} className="space-y-3 text-xs">
                <div>
                  <label className="block text-text-secondary font-medium mb-1">
                    Decision Title <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={decisionTitle}
                    onChange={(e) => setDecisionTitle(e.target.value)}
                    placeholder="e.g. Adopt PostgreSQL for Authoritative State"
                    className="w-full bg-surface border border-border text-text-primary rounded-lg px-3 py-2 focus:outline-none focus:border-primary"
                  />
                </div>

                <div>
                  <label className="block text-text-secondary font-medium mb-1">
                    Authoritative Determination / Outcome <span className="text-red-400">*</span>
                  </label>
                  <textarea
                    required
                    rows={3}
                    value={decisionOutcome}
                    onChange={(e) => setDecisionOutcome(e.target.value)}
                    placeholder="Clear, authoritative statement of what was decided..."
                    className="w-full bg-surface border border-border text-text-primary rounded-lg px-3 py-2 focus:outline-none focus:border-primary"
                  />
                </div>

                <div>
                  <label className="block text-text-secondary font-medium mb-1">
                    Rationale & Justification <span className="text-red-400">*</span>
                  </label>
                  <textarea
                    required
                    rows={2}
                    value={decisionRationale}
                    onChange={(e) => setDecisionRationale(e.target.value)}
                    placeholder="Why this determination was made, evidence, tradeoffs..."
                    className="w-full bg-surface border border-border text-text-primary rounded-lg px-3 py-2 focus:outline-none focus:border-primary"
                  />
                </div>

                <div>
                  <label className="block text-text-secondary font-medium mb-1">
                    Associated Project ID (Optional)
                  </label>
                  <input
                    type="text"
                    value={decisionProjectId}
                    onChange={(e) => setDecisionProjectId(e.target.value)}
                    placeholder="Optional project UUID to scope decision..."
                    className="w-full bg-surface border border-border text-text-primary rounded-lg px-3 py-2 focus:outline-none focus:border-primary font-mono text-[11px]"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
                  <button
                    type="button"
                    onClick={() => {
                      setShowRecordModal(false);
                      setSupersedingTarget(null);
                    }}
                    className="px-3 py-2 rounded-lg bg-surface border border-border text-text-secondary hover:text-text-primary transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={recordingDecision}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white font-semibold shadow-sm transition disabled:opacity-50"
                  >
                    {recordingDecision ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        Persisting Decision...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Save Decision
                      </>
                    )}
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
