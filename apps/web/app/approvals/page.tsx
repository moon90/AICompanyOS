"use client";

import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Building2,
  CheckCircle2,
  Clock,
  ExternalLink,
  Eye,
  Filter,
  RefreshCw,
  Shield,
  ShieldAlert,
  ShieldCheck,
  User as UserIcon,
  X,
  XCircle,
} from "lucide-react";
import {
  api,
  ApprovalRequest,
  Company,
} from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

export default function ApprovalsPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [activeCompany, setActiveCompany] = useState<Company | null>(null);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [riskFilter, setRiskFilter] = useState<string>("ALL");

  // Detail Drawer & Decision Modal
  const [selectedApproval, setSelectedApproval] = useState<ApprovalRequest | null>(null);
  const [decisionModalMode, setDecisionModalMode] = useState<"APPROVE" | "REJECT" | null>(null);
  const [decisionTarget, setDecisionTarget] = useState<ApprovalRequest | null>(null);
  const [decisionReason, setDecisionReason] = useState("");
  const [submittingDecision, setSubmittingDecision] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    loadInitialData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadInitialData() {
    setLoading(true);
    try {
      const companyList = await api.getCompanies();
      setCompanies(companyList);
      const primary = companyList[0] || null;
      setActiveCompany(primary);
      if (primary) {
        await loadApprovals(primary.id);
      }
    } catch (err) {
      console.error("Failed loading company list for approvals:", err);
    } finally {
      setLoading(false);
    }
  }

  async function loadApprovals(companyId: string) {
    setRefreshing(true);
    setActionMessage(null);
    try {
      const resp = await api.getApprovals(companyId, { limit: 100 });
      setApprovals(resp.items);
    } catch (err) {
      console.error("Failed loading approvals:", err);
    } finally {
      setRefreshing(false);
    }
  }

  function handleCompanyChange(companyId: string) {
    const selected = companies.find((c) => c.id === companyId) || null;
    setActiveCompany(selected);
    if (selected) {
      loadApprovals(selected.id);
    }
  }

  function openDecisionModal(approval: ApprovalRequest, mode: "APPROVE" | "REJECT") {
    setDecisionTarget(approval);
    setDecisionModalMode(mode);
    setDecisionReason("");
    setActionMessage(null);
  }

  function closeDecisionModal() {
    setDecisionModalMode(null);
    setDecisionTarget(null);
    setDecisionReason("");
  }

  async function handleConfirmDecision() {
    if (!activeCompany || !decisionTarget || !decisionModalMode) return;

    setSubmittingDecision(true);
    setActionMessage(null);
    try {
      if (decisionModalMode === "APPROVE") {
        const updated = await api.approveRequest(activeCompany.id, decisionTarget.id, {
          decision_reason: decisionReason.trim() || undefined,
        });
        setActionMessage({
          type: "success",
          text: `Action '${updated.action_type}' has been approved and executed.`,
        });
      } else {
        const updated = await api.rejectRequest(activeCompany.id, decisionTarget.id, {
          decision_reason: decisionReason.trim() || undefined,
        });
        setActionMessage({
          type: "success",
          text: `Action '${updated.action_type}' has been rejected and permanently blocked.`,
        });
      }
      closeDecisionModal();
      await loadApprovals(activeCompany.id);
    } catch (err: unknown) {
      const errorDetail = err instanceof Error ? err.message : "Failed to submit decision.";
      setActionMessage({
        type: "error",
        text: errorDetail,
      });
    } finally {
      setSubmittingDecision(false);
    }
  }

  // Filtered dataset
  const filteredApprovals = approvals.filter((a) => {
    if (statusFilter !== "ALL" && a.status !== statusFilter) return false;
    if (riskFilter !== "ALL" && a.risk_level !== riskFilter) return false;
    return true;
  });

  // Metrics computation
  const pendingCount = approvals.filter((a) => a.status === "PENDING").length;
  const approvedCount = approvals.filter((a) => a.status === "APPROVED").length;
  const rejectedCount = approvals.filter((a) => a.status === "REJECTED").length;
  const highRiskPending = approvals.filter(
    (a) => a.status === "PENDING" && (a.risk_level === "CRITICAL" || a.risk_level === "HIGH")
  ).length;

  return (
    <ShellLayout pageTitle="Approvals" breadcrumb="Work Management">
      <div className="space-y-6 max-w-7xl mx-auto pb-16">
        {/* Top Header & Company Selector */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#0d121c] border border-[#1e2738] p-5 rounded-2xl shadow-xl">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/25 flex items-center justify-center text-amber-400">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-white tracking-tight">
                  Human Oversight & Approvals
                </h1>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-amber-500/15 border border-amber-500/30 text-amber-300">
                  Phase 10 Active
                </span>
              </div>
              <p className="text-sm text-slate-400">
                Authoritative human approval gate for consequential agent actions and high-risk tool operations.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-[#121824] border border-[#1e2738] px-3 py-1.5 rounded-lg">
              <Building2 className="w-4 h-4 text-slate-400" />
              <select
                className="bg-transparent text-sm text-white focus:outline-none cursor-pointer"
                value={activeCompany?.id || ""}
                onChange={(e) => handleCompanyChange(e.target.value)}
                disabled={loading || companies.length === 0}
              >
                {companies.map((c) => (
                  <option key={c.id} value={c.id} className="bg-[#121824] text-white">
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => activeCompany && loadApprovals(activeCompany.id)}
              disabled={refreshing || !activeCompany}
              className="p-2 rounded-lg bg-[#121824] border border-[#1e2738] hover:bg-[#1a2333] text-slate-300 transition-colors disabled:opacity-50"
              title="Refresh approvals"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin text-amber-400" : ""}`} />
            </button>
          </div>
        </div>

        {/* Global Feedback Alert */}
        {actionMessage && (
          <div
            className={`p-4 rounded-xl border flex items-center justify-between gap-3 ${
              actionMessage.type === "success"
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                : "bg-rose-500/10 border-rose-500/30 text-rose-300"
            }`}
          >
            <div className="flex items-center gap-3">
              {actionMessage.type === "success" ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              ) : (
                <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
              )}
              <span className="text-sm font-medium">{actionMessage.text}</span>
            </div>
            <button
              onClick={() => setActionMessage(null)}
              className="text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Telemetry Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[#0d121c] border border-[#1e2738] p-5 rounded-2xl relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase font-mono font-medium text-slate-400">
                Pending Actions
              </span>
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/25 flex items-center justify-center text-amber-400">
                <Clock className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono text-white">{pendingCount}</span>
              {pendingCount > 0 && (
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse">
                  Requires Review
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-1">Awaiting human operator sign-off</p>
          </div>

          <div className="bg-[#0d121c] border border-[#1e2738] p-5 rounded-2xl relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase font-mono font-medium text-slate-400">
                High / Critical Risk
              </span>
              <div className="w-8 h-8 rounded-lg bg-rose-500/10 border border-rose-500/25 flex items-center justify-center text-rose-400">
                <ShieldAlert className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono text-white">{highRiskPending}</span>
              <span className="text-xs text-slate-400">pending</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">Consequential decisions requiring caution</p>
          </div>

          <div className="bg-[#0d121c] border border-[#1e2738] p-5 rounded-2xl relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase font-mono font-medium text-slate-400">
                Total Approved
              </span>
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-400">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono text-emerald-400">{approvedCount}</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">Authorized and released to execution</p>
          </div>

          <div className="bg-[#0d121c] border border-[#1e2738] p-5 rounded-2xl relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase font-mono font-medium text-slate-400">
                Total Rejected
              </span>
              <div className="w-8 h-8 rounded-lg bg-rose-500/10 border border-rose-500/25 flex items-center justify-center text-rose-400">
                <XCircle className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono text-rose-400">{rejectedCount}</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">Permanently blocked consequential actions</p>
          </div>
        </div>

        {/* Filter Bar & Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#0d121c] border border-[#1e2738] p-4 rounded-2xl">
          {/* Status Tabs */}
          <div className="flex items-center gap-1 bg-[#121824] p-1 rounded-xl border border-[#1e2738]">
            {(["ALL", "PENDING", "APPROVED", "REJECTED"] as const).map((tab) => {
              const active = statusFilter === tab;
              const badgeCount =
                tab === "ALL"
                  ? approvals.length
                  : tab === "PENDING"
                  ? pendingCount
                  : tab === "APPROVED"
                  ? approvedCount
                  : rejectedCount;

              return (
                <button
                  key={tab}
                  onClick={() => setStatusFilter(tab)}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
                    active
                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow"
                      : "text-slate-400 hover:text-white hover:bg-[#1a2333]"
                  }`}
                >
                  <span>{tab}</span>
                  <span
                    className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                      active ? "bg-amber-500/30 text-amber-200" : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {badgeCount}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Risk Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-xs text-slate-400">Risk Tier:</span>
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="bg-[#121824] border border-[#1e2738] text-xs text-white px-3 py-1.5 rounded-lg focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Risk Tiers</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>

        {/* Approvals List */}
        {loading ? (
          <div className="flex items-center justify-center p-16 bg-[#0d121c] border border-[#1e2738] rounded-2xl">
            <div className="flex flex-col items-center gap-3">
              <RefreshCw className="w-8 h-8 text-amber-400 animate-spin" />
              <p className="text-sm text-slate-400 font-mono">Loading approval requests...</p>
            </div>
          </div>
        ) : filteredApprovals.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-16 bg-[#0d121c] border border-[#1e2738] rounded-2xl text-center">
            <div className="w-14 h-14 rounded-2xl bg-slate-800/50 border border-slate-700/50 flex items-center justify-center text-slate-400 mb-3">
              <ShieldCheck className="w-7 h-7" />
            </div>
            <h3 className="text-base font-semibold text-white">No Approval Requests</h3>
            <p className="text-sm text-slate-400 max-w-sm mt-1">
              {statusFilter === "PENDING"
                ? "All clear! There are currently no pending consequential actions requiring review."
                : "No approval requests match the currently applied status and risk filters."}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredApprovals.map((req) => {
              const isPending = req.status === "PENDING";
              const isApproved = req.status === "APPROVED";
              const isRejected = req.status === "REJECTED";

              return (
                <div
                  key={req.id}
                  className={`bg-[#0d121c] border transition-all rounded-2xl p-5 ${
                    isPending
                      ? "border-amber-500/30 hover:border-amber-500/50 bg-gradient-to-r from-[#0d121c] via-[#0d121c] to-amber-950/10 shadow-lg"
                      : "border-[#1e2738] hover:border-slate-700"
                  }`}
                >
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    {/* Left: Action Summary & Badges */}
                    <div className="space-y-2 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        {/* Status Badge */}
                        {isPending ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/15 border border-amber-500/30 text-amber-300">
                            <Clock className="w-3.5 h-3.5 animate-spin" />
                            Pending Review
                          </span>
                        ) : isApproved ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/15 border border-emerald-500/30 text-emerald-300">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Approved
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/15 border border-rose-500/30 text-rose-300">
                            <XCircle className="w-3.5 h-3.5" />
                            Rejected
                          </span>
                        )}

                        {/* Risk Tier Badge */}
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold ${
                            req.risk_level === "CRITICAL"
                              ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                              : req.risk_level === "HIGH"
                              ? "bg-orange-500/20 text-orange-300 border border-orange-500/40"
                              : req.risk_level === "MEDIUM"
                              ? "bg-yellow-500/20 text-yellow-300 border border-yellow-500/40"
                              : "bg-blue-500/20 text-blue-300 border border-blue-500/40"
                          }`}
                        >
                          <Shield className="w-3 h-3" />
                          {req.risk_level} RISK
                        </span>

                        {/* Action Type */}
                        <span className="font-mono text-xs text-slate-300 font-semibold px-2 py-0.5 rounded bg-[#161d2d] border border-[#26334a]">
                          {req.action_type}
                        </span>

                        {/* Tool Identifier if present */}
                        {req.tool_name && (
                          <span className="text-xs font-mono text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded">
                            Tool: {req.tool_name}
                          </span>
                        )}
                      </div>

                      {/* Description */}
                      <p className="text-sm text-white font-medium">{req.description}</p>

                      {/* Metadata Row: Agent, Task, Reviewer */}
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
                        {req.agent_name && (
                          <span className="flex items-center gap-1 text-slate-300">
                            <UserIcon className="w-3.5 h-3.5 text-slate-400" />
                            Requesting Agent: <strong className="text-white">{req.agent_name}</strong>
                          </span>
                        )}
                        {req.task_title && (
                          <span className="text-slate-300">
                            Linked Task: <strong className="text-slate-200">{req.task_title}</strong>
                          </span>
                        )}
                        <span>Submitted: {new Date(req.created_at).toLocaleString()}</span>
                        {req.reviewed_at && (
                          <span className="text-emerald-400">
                            Reviewed: {new Date(req.reviewed_at).toLocaleString()}{" "}
                            {req.reviewer_name ? `by ${req.reviewer_name}` : ""}
                          </span>
                        )}
                      </div>

                      {/* Decision Reason Quote if present */}
                      {req.decision_reason && (
                        <div className="mt-2 p-2.5 rounded-lg bg-[#141b29] border border-[#202b3d] text-xs text-slate-300 flex items-start gap-2">
                          <span className="font-semibold text-slate-400 shrink-0">Operator Note:</span>
                          <span className="italic">{req.decision_reason}</span>
                        </div>
                      )}
                    </div>

                    {/* Right: Actions */}
                    <div className="flex items-center gap-2 self-start lg:self-center shrink-0">
                      <button
                        onClick={() => setSelectedApproval(req)}
                        className="px-3 py-2 rounded-xl bg-[#121824] border border-[#1e2738] hover:bg-[#1a2333] text-slate-300 hover:text-white text-xs font-medium transition-colors flex items-center gap-1.5"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        Details
                      </button>

                      {isPending && (
                        <>
                          <button
                            onClick={() => openDecisionModal(req, "APPROVE")}
                            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950/40 transition-all flex items-center gap-1.5"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Approve
                          </button>

                          <button
                            onClick={() => openDecisionModal(req, "REJECT")}
                            className="px-4 py-2 rounded-xl bg-rose-600/20 border border-rose-500/40 hover:bg-rose-600 text-rose-300 hover:text-white text-xs font-semibold transition-all flex items-center gap-1.5"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            Reject
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Decision Modal (Approve or Reject) */}
        {decisionModalMode && decisionTarget && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
            <div className="bg-[#0f1420] border border-[#1e2738] rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#1e2738]">
                <div className="flex items-center gap-2.5">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                      decisionModalMode === "APPROVE"
                        ? "bg-emerald-500/15 border border-emerald-500/30 text-emerald-400"
                        : "bg-rose-500/15 border border-rose-500/30 text-rose-400"
                    }`}
                  >
                    {decisionModalMode === "APPROVE" ? (
                      <CheckCircle2 className="w-5 h-5" />
                    ) : (
                      <XCircle className="w-5 h-5" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">
                      {decisionModalMode === "APPROVE"
                        ? "Authorize Consequential Action"
                        : "Reject Consequential Action"}
                    </h3>
                    <p className="text-xs text-slate-400">
                      {decisionModalMode === "APPROVE"
                        ? "Execution will immediately resume with operator sign-off."
                        : "Action will be permanently halted and gated adapter will not execute."}
                    </p>
                  </div>
                </div>
                <button
                  onClick={closeDecisionModal}
                  className="text-slate-400 hover:text-white p-1 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Action Details Summary */}
              <div className="space-y-2 p-3.5 rounded-xl bg-[#141b2a] border border-[#202b3d] text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Action:</span>
                  <span className="font-mono text-white font-semibold">
                    {decisionTarget.action_type}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Risk Tier:</span>
                  <span
                    className={`font-semibold ${
                      decisionTarget.risk_level === "CRITICAL"
                        ? "text-rose-400"
                        : decisionTarget.risk_level === "HIGH"
                        ? "text-orange-400"
                        : "text-amber-400"
                    }`}
                  >
                    {decisionTarget.risk_level}
                  </span>
                </div>
                {decisionTarget.agent_name && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Requesting Agent:</span>
                    <span className="text-white">{decisionTarget.agent_name}</span>
                  </div>
                )}
                {decisionTarget.task_title && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Task Context:</span>
                    <span className="text-slate-200">{decisionTarget.task_title}</span>
                  </div>
                )}
                <div className="pt-2 border-t border-[#1e2738]">
                  <span className="text-slate-400 block mb-1">Description:</span>
                  <p className="text-white">{decisionTarget.description}</p>
                </div>
              </div>

              {/* Justification Textarea */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 block">
                  Reviewer Justification / Notes
                  <span className="text-slate-500 font-normal ml-1">
                    {decisionModalMode === "APPROVE" ? "(Optional)" : "(Recommended)"}
                  </span>
                </label>
                <textarea
                  value={decisionReason}
                  onChange={(e) => setDecisionReason(e.target.value)}
                  placeholder={
                    decisionModalMode === "APPROVE"
                      ? "e.g., Code reviewed, budget verified with finance team."
                      : "e.g., Pull request failed security inspection, budget limit exceeded."
                  }
                  rows={3}
                  className="w-full bg-[#141b2a] border border-[#202b3d] rounded-xl p-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              {/* Modal Buttons */}
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  onClick={closeDecisionModal}
                  disabled={submittingDecision}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-[#1a2333] transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmDecision}
                  disabled={submittingDecision}
                  className={`px-5 py-2 rounded-xl text-xs font-semibold text-white shadow-lg transition-all flex items-center gap-1.5 ${
                    decisionModalMode === "APPROVE"
                      ? "bg-emerald-600 hover:bg-emerald-500 shadow-emerald-950/50"
                      : "bg-rose-600 hover:bg-rose-500 shadow-rose-950/50"
                  } disabled:opacity-50`}
                >
                  {submittingDecision ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      Processing...
                    </>
                  ) : decisionModalMode === "APPROVE" ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Authorize & Execute
                    </>
                  ) : (
                    <>
                      <XCircle className="w-3.5 h-3.5" />
                      Permanently Block
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Details Drawer */}
        {selectedApproval && (
          <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/60 backdrop-blur-sm">
            <div className="bg-[#0f1420] border-l border-[#1e2738] w-full max-w-xl h-full shadow-2xl p-6 overflow-y-auto space-y-5 animate-in slide-in-from-right duration-200">
              <div className="flex items-center justify-between pb-3 border-b border-[#1e2738]">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-amber-400" />
                  <h3 className="text-base font-bold text-white">Approval Record Details</h3>
                </div>
                <button
                  onClick={() => setSelectedApproval(null)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-[#1a2333]"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Status Header */}
              <div className="p-4 rounded-xl bg-[#141b2a] border border-[#202b3d] space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-mono">APPROVAL ID</span>
                  <span className="text-xs font-mono text-slate-300 font-bold">
                    {selectedApproval.id}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-mono">STATUS</span>
                  <span
                    className={`text-xs font-bold font-mono px-2 py-0.5 rounded ${
                      selectedApproval.status === "PENDING"
                        ? "bg-amber-500/20 text-amber-300"
                        : selectedApproval.status === "APPROVED"
                        ? "bg-emerald-500/20 text-emerald-300"
                        : "bg-rose-500/20 text-rose-300"
                    }`}
                  >
                    {selectedApproval.status}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-mono">RISK LEVEL</span>
                  <span className="text-xs font-bold font-mono text-white">
                    {selectedApproval.risk_level}
                  </span>
                </div>
              </div>

              {/* Action Info */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 font-mono">
                  Action Overview
                </h4>
                <div className="p-3.5 rounded-xl bg-[#141b2a] border border-[#202b3d] space-y-2 text-xs">
                  <div>
                    <span className="text-slate-400 block">Action Type:</span>
                    <span className="font-mono text-white font-semibold">
                      {selectedApproval.action_type}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Description:</span>
                    <span className="text-white">{selectedApproval.description}</span>
                  </div>
                  {selectedApproval.tool_name && (
                    <div>
                      <span className="text-slate-400 block">Target Tool Gateway:</span>
                      <span className="text-indigo-400 font-mono">{selectedApproval.tool_name}</span>
                    </div>
                  )}
                  {selectedApproval.agent_name && (
                    <div>
                      <span className="text-slate-400 block">Requesting Agent:</span>
                      <span className="text-white">{selectedApproval.agent_name}</span>
                    </div>
                  )}
                  {selectedApproval.task_title && (
                    <div>
                      <span className="text-slate-400 block">Associated Task:</span>
                      <span className="text-slate-200">{selectedApproval.task_title}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Payload Parameters */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 font-mono">
                  Payload Parameters (JSON)
                </h4>
                <pre className="p-3.5 rounded-xl bg-[#090d14] border border-[#1e2738] text-[11px] font-mono text-emerald-400 overflow-x-auto">
                  {JSON.stringify(selectedApproval.payload, null, 2)}
                </pre>
              </div>

              {/* Audit Timestamps & Reviewer */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 font-mono">
                  Audit History
                </h4>
                <div className="p-3.5 rounded-xl bg-[#141b2a] border border-[#202b3d] space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Created At:</span>
                    <span className="text-white">
                      {new Date(selectedApproval.created_at).toLocaleString()}
                    </span>
                  </div>
                  {selectedApproval.reviewed_at && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">Reviewed At:</span>
                      <span className="text-white">
                        {new Date(selectedApproval.reviewed_at).toLocaleString()}
                      </span>
                    </div>
                  )}
                  {selectedApproval.reviewer_name && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">Reviewed By:</span>
                      <span className="text-white font-semibold">
                        {selectedApproval.reviewer_name}
                      </span>
                    </div>
                  )}
                  {selectedApproval.decision_reason && (
                    <div className="pt-2 border-t border-[#1e2738]">
                      <span className="text-slate-400 block mb-1">Decision Justification:</span>
                      <p className="text-white italic">&ldquo;{selectedApproval.decision_reason}&rdquo;</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Footer Buttons if Pending */}
              {selectedApproval.status === "PENDING" && (
                <div className="flex items-center gap-3 pt-4 border-t border-[#1e2738]">
                  <button
                    onClick={() => {
                      const target = selectedApproval;
                      setSelectedApproval(null);
                      openDecisionModal(target, "APPROVE");
                    }}
                    className="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950/40 flex items-center justify-center gap-2"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Approve Action
                  </button>
                  <button
                    onClick={() => {
                      const target = selectedApproval;
                      setSelectedApproval(null);
                      openDecisionModal(target, "REJECT");
                    }}
                    className="flex-1 py-2.5 rounded-xl bg-rose-600/20 border border-rose-500/40 hover:bg-rose-600 text-rose-300 hover:text-white text-xs font-semibold flex items-center justify-center gap-2"
                  >
                    <XCircle className="w-4 h-4" />
                    Reject Action
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </ShellLayout>
  );
}
