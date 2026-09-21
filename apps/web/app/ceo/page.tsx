"use client";

import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Bot,
  Building2,
  CheckCircle2,
  Clock,
  ExternalLink,
  GitBranch,
  History,
  Layers,
  ListTodo,
  Loader2,
  Send,
  Shield,
  ShieldAlert,
  Sparkles,
  Users,
} from "lucide-react";
import Link from "next/link";
import {
  api,
  CeoContext,
  CeoPlanDetail,
  CeoPlanSummary,
  Company,
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

  // Form State
  const [objective, setObjective] = useState("");
  const [requestedOutcome, setRequestedOutcome] = useState("");
  const [priority, setPriority] = useState<"low" | "medium" | "high" | "critical">("high");
  const [constraintsText, setConstraintsText] = useState("");
  const [requirementsText, setRequirementsText] = useState("");

  const [loading, setLoading] = useState(true);
  const [planning, setPlanning] = useState(false);
  const [planLoading, setPlanLoading] = useState(false);
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
  }, [activeCompany, loadPlanDetail]);

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
      setError(err.message || "Failed to synthesize plan");
    } finally {
      setPlanning(false);
    }
  }

  if (loading) {
    return (
      <ShellLayout pageTitle="CEO Orchestrator" breadcrumb="Executive">
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      </ShellLayout>
    );
  }

  if (companies.length === 0) {
    return (
      <ShellLayout pageTitle="CEO Orchestrator" breadcrumb="Executive">
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
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-surface-card border border-border flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                <Bot className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-semibold text-text-primary">{ceo.name}</h2>
                  <span className="px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Authority Level 5
                  </span>
                  <span className="px-1.5 py-0.5 text-[10px] rounded bg-surface-elevated text-text-secondary border border-border">
                    Planning Mode
                  </span>
                </div>
                <p className="text-xs text-text-muted mt-0.5">
                  Primary Strategic Orchestrator · Directs Executive & Department Coordination
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

        {/* Main Workspace Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Goal Intake & Plan History (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            {/* CEO Command Box */}
            <div className="p-5 rounded-xl bg-surface-card border border-border space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary" />
                  <h3 className="text-sm font-semibold text-text-primary">
                    Strategic Goal Intake
                  </h3>
                </div>
                <span className="text-[11px] text-text-muted">
                  Orchestrator Foundation
                </span>
              </div>

              <form onSubmit={handleCreatePlan} className="space-y-3.5">
                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1">
                    Executive Objective *
                  </label>
                  <textarea
                    rows={3}
                    required
                    disabled={!ceo || planning}
                    value={objective}
                    onChange={(e) => setObjective(e.target.value)}
                    placeholder="e.g. Research whether we should launch our product in Germany..."
                    className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary disabled:opacity-50 resize-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1">
                    Requested Outcome (Optional)
                  </label>
                  <input
                    type="text"
                    disabled={!ceo || planning}
                    value={requestedOutcome}
                    onChange={(e) => setRequestedOutcome(e.target.value)}
                    placeholder="e.g. Executive report with technical and market recommendations"
                    className="w-full bg-surface border border-border rounded-lg px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary disabled:opacity-50"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-text-secondary mb-1">
                      Priority
                    </label>
                    <select
                      disabled={!ceo || planning}
                      value={priority}
                      onChange={(e: any) => setPriority(e.target.value)}
                      className="w-full bg-surface border border-border rounded-lg px-2.5 py-1.5 text-xs text-text-primary focus:outline-none focus:border-primary disabled:opacity-50"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-text-secondary mb-1">
                      Safety Guardrail
                    </label>
                    <div className="px-2.5 py-1.5 bg-surface border border-border rounded-lg text-xs text-text-muted flex items-center gap-1.5">
                      <Shield className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      <span className="truncate">Proposal Only</span>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1">
                    Constraints (1 per line)
                  </label>
                  <textarea
                    rows={2}
                    disabled={!ceo || planning}
                    value={constraintsText}
                    onChange={(e) => setConstraintsText(e.target.value)}
                    placeholder="e.g. Do not spend money&#10;Complete within 14 days"
                    className="w-full bg-surface border border-border rounded-lg px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary disabled:opacity-50 resize-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={!ceo || planning || !objective.trim()}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-black font-semibold text-xs rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
                >
                  {planning ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Synthesizing Plan & DAG...
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      Decompose & Synthesize Plan
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* Plan History List */}
            <div className="p-5 rounded-xl bg-surface-card border border-border space-y-3">
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
                <div className="p-3.5 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-start gap-3 text-xs">
                  <ShieldAlert className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-blue-300">
                      Recommendation & Proposal Contract:
                    </span>{" "}
                    <span className="text-text-secondary">
                      This plan is a structured proposal synthesized by the CEO. It does not invoke agents or execute tasks until human governance approval and Phase 6 task engine integration.
                    </span>
                  </div>
                </div>

                {/* Plan Overview Card */}
                <div className="p-5 rounded-xl bg-surface-card border border-border space-y-3">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          Status: {selectedPlan.status}
                        </span>
                        <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                          Priority: {selectedPlan.priority}
                        </span>
                      </div>
                      <h2 className="text-base font-semibold text-text-primary">
                        {selectedPlan.goal}
                      </h2>
                    </div>
                  </div>

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
                    Delegation Proposals ({selectedPlan.delegation_proposals.length})
                  </button>
                  <button
                    onClick={() => setActiveTab("governance")}
                    className={`flex items-center gap-2 px-4 py-2.5 font-medium border-b-2 transition-colors ${
                      activeTab === "governance"
                        ? "border-primary text-text-primary"
                        : "border-transparent text-text-muted hover:text-text-secondary"
                    }`}
                  >
                    <Shield className="w-3.5 h-3.5" />
                    Governance & Risks ({selectedPlan.approval_requirements.length + selectedPlan.risks.length})
                  </button>
                </div>

                {/* Tab 1: Task Graph DAG Steps */}
                {activeTab === "dag" && (
                  <div className="space-y-3">
                    {selectedPlan.plan_steps.map((step, idx) => (
                      <div
                        key={step.step_id}
                        className="p-4 rounded-xl bg-surface-card border border-border space-y-2.5 relative"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="w-6 h-6 rounded-full bg-surface-elevated border border-border flex items-center justify-center text-[11px] font-mono font-semibold text-text-primary">
                              {idx + 1}
                            </span>
                            <h4 className="text-xs font-semibold text-text-primary">
                              {step.title}
                            </h4>
                            <span className="font-mono text-[10px] text-text-muted">
                              ({step.step_id})
                            </span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            {step.department_code && (
                              <span className="px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                                {step.department_code}
                              </span>
                            )}
                            <span className="px-2 py-0.5 text-[10px] rounded bg-surface-elevated text-text-secondary border border-border font-medium">
                              Role: {step.assigned_agent_role}
                            </span>
                          </div>
                        </div>

                        <p className="text-xs text-text-secondary leading-relaxed">
                          {step.description}
                        </p>

                        {/* Dependencies */}
                        {step.depends_on.length > 0 && (
                          <div className="flex items-center gap-1.5 flex-wrap text-[11px]">
                            <span className="text-text-muted">Depends on:</span>
                            {step.depends_on.map((dep) => (
                              <span
                                key={dep}
                                className="px-1.5 py-0.5 rounded bg-surface border border-border font-mono text-[10px] text-primary"
                              >
                                {dep}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Deliverables & Criteria */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 text-[11px]">
                          <div className="bg-surface p-2 rounded border border-border">
                            <span className="text-text-muted block font-medium mb-0.5">
                              Expected Deliverable:
                            </span>
                            <span className="text-text-secondary">{step.expected_output}</span>
                          </div>
                          <div className="bg-surface p-2 rounded border border-border">
                            <span className="text-text-muted block font-medium mb-0.5">
                              Verification Criteria:
                            </span>
                            <span className="text-text-secondary">
                              {step.verification_criteria}
                            </span>
                          </div>
                        </div>

                        {/* Required Capabilities */}
                        {step.required_capabilities.length > 0 && (
                          <div className="flex items-center gap-1.5 flex-wrap pt-1">
                            <span className="text-[10px] text-text-muted">Capabilities:</span>
                            {step.required_capabilities.map((cap) => (
                              <span
                                key={cap}
                                className="px-1.5 py-0.5 text-[10px] rounded bg-surface-elevated text-text-muted border border-border"
                              >
                                {cap}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Tab 2: Delegation Proposals */}
                {activeTab === "delegation" && (
                  <div className="space-y-3">
                    {selectedPlan.delegation_proposals.length === 0 ? (
                      <p className="text-xs text-text-muted text-center py-8">
                        No delegation proposals generated for this plan.
                      </p>
                    ) : (
                      selectedPlan.delegation_proposals.map((prop) => (
                        <div
                          key={prop.proposal_id}
                          className="p-4 rounded-xl bg-surface-card border border-border space-y-2 text-xs"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-text-primary">
                                CEO → {prop.target_role.toUpperCase()}
                              </span>
                              <span className="text-text-muted font-mono text-[10px]">
                                ({prop.proposal_id})
                              </span>
                            </div>
                            <span className="px-1.5 py-0.5 text-[10px] rounded bg-surface-elevated text-text-secondary border border-border">
                              Req. Authority: L{prop.authority_level_required}
                            </span>
                          </div>

                          <div>
                            <span className="text-text-muted font-medium">Objective:</span>{" "}
                            <span className="text-text-secondary">{prop.objective}</span>
                          </div>

                          <div>
                            <span className="text-text-muted font-medium">Delegated Scope:</span>{" "}
                            <span className="text-text-secondary">{prop.scope}</span>
                          </div>

                          <div>
                            <span className="text-text-muted font-medium">Expected Output:</span>{" "}
                            <span className="text-text-secondary">{prop.expected_output}</span>
                          </div>

                          {prop.required_capabilities.length > 0 && (
                            <div className="flex items-center gap-1.5 flex-wrap pt-1">
                              <span className="text-text-muted text-[10px]">Capabilities:</span>
                              {prop.required_capabilities.map((c) => (
                                <span
                                  key={c}
                                  className="px-1.5 py-0.5 text-[10px] rounded bg-surface border border-border text-text-muted"
                                >
                                  {c}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* Tab 3: Governance Gates & Risk Matrix */}
                {activeTab === "governance" && (
                  <div className="space-y-4 text-xs">
                    {/* Approval Requirements */}
                    <div className="p-4 rounded-xl bg-surface-card border border-border space-y-3">
                      <div className="flex items-center gap-2">
                        <Shield className="w-4 h-4 text-amber-400" />
                        <h4 className="font-semibold text-text-primary">
                          Mandatory Governance Approval Gates
                        </h4>
                      </div>

                      {selectedPlan.approval_requirements.length === 0 ? (
                        <p className="text-text-muted text-[11px]">
                          No manual approval gates flagged for this plan.
                        </p>
                      ) : (
                        <div className="space-y-2">
                          {selectedPlan.approval_requirements.map((app, idx) => (
                            <div
                              key={idx}
                              className="p-3 rounded-lg bg-surface border border-border space-y-1"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-medium text-text-primary">
                                  Gate for {app.step_id}
                                </span>
                                <span className="px-1.5 py-0.5 text-[10px] font-semibold uppercase rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
                                  Risk: {app.risk_level}
                                </span>
                              </div>
                              <p className="text-text-secondary text-[11px]">
                                {app.action_description}
                              </p>
                              <p className="text-text-muted text-[10px] italic">
                                Reason: {app.reason_for_approval}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Risk Analysis */}
                    <div className="p-4 rounded-xl bg-surface-card border border-border space-y-3">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-text-secondary" />
                        <h4 className="font-semibold text-text-primary">
                          Identified Risks & Mitigations
                        </h4>
                      </div>
                      <div className="space-y-2">
                        {selectedPlan.risks.map((r, idx) => (
                          <div
                            key={idx}
                            className="p-3 rounded-lg bg-surface border border-border space-y-1 text-[11px]"
                          >
                            <div className="font-medium text-red-300">Risk: {r.risk}</div>
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
      </div>
    </ShellLayout>
  );
}
