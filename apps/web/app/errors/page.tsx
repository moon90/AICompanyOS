"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  AlertOctagon,
  ArrowRight,
  Bot,
  Bug,
  CheckCircle2,
  Clock,
  ExternalLink,
  Eye,
  FileCheck2,
  Filter,
  FolderGit2,
  Layers,
  Loader2,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldAlert,
  Sparkles,
  User as UserIcon,
  Users,
  Wrench,
  X,
} from "lucide-react";
import Link from "next/link";
import {
  Agent,
  api,
  Company,
  ErrorCreatePayload,
  ErrorRecord,
  ErrorSeverity,
  ErrorStatus,
  ErrorSummary,
  Project,
  Task,
} from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

const SEVERITY_CONFIG: Record<
  ErrorSeverity,
  { label: string; bg: string; text: string; border: string; icon: React.ComponentType<{ className?: string }> }
> = {
  CRITICAL: {
    label: "Critical",
    bg: "bg-rose-500/10",
    text: "text-rose-400",
    border: "border-rose-500/30",
    icon: AlertOctagon,
  },
  HIGH: {
    label: "High",
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/30",
    icon: AlertCircle,
  },
  MEDIUM: {
    label: "Medium",
    bg: "bg-blue-500/10",
    text: "text-blue-400",
    border: "border-blue-500/30",
    icon: Bug,
  },
  LOW: {
    label: "Low",
    bg: "bg-slate-500/10",
    text: "text-slate-400",
    border: "border-slate-500/30",
    icon: Layers,
  },
};

const STATUS_CONFIG: Record<
  ErrorStatus,
  { label: string; bg: string; text: string; border: string }
> = {
  OPEN: {
    label: "Open",
    bg: "bg-blue-500/10",
    text: "text-blue-400",
    border: "border-blue-500/25",
  },
  TRIAGED: {
    label: "Triaged",
    bg: "bg-sky-500/10",
    text: "text-sky-400",
    border: "border-sky-500/25",
  },
  ASSIGNED: {
    label: "Assigned",
    bg: "bg-indigo-500/10",
    text: "text-indigo-400",
    border: "border-indigo-500/25",
  },
  INVESTIGATING: {
    label: "Investigating",
    bg: "bg-purple-500/10",
    text: "text-purple-400",
    border: "border-purple-500/25",
  },
  BLOCKED: {
    label: "Blocked",
    bg: "bg-rose-500/10",
    text: "text-rose-400",
    border: "border-rose-500/25",
  },
  RESOLVED: {
    label: "Resolved",
    bg: "bg-teal-500/10",
    text: "text-teal-400",
    border: "border-teal-500/25",
  },
  VERIFYING: {
    label: "Verifying",
    bg: "bg-cyan-500/10",
    text: "text-cyan-400",
    border: "border-cyan-500/25",
  },
  VERIFIED: {
    label: "Verified",
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/25",
  },
  REOPENED: {
    label: "Reopened",
    bg: "bg-orange-500/10",
    text: "text-orange-400",
    border: "border-orange-500/25",
  },
  CLOSED: {
    label: "Closed",
    bg: "bg-slate-500/10",
    text: "text-slate-400",
    border: "border-slate-500/25",
  },
};

export default function ErrorsPage() {
  const [company, setCompany] = useState<Company | null>(null);
  const [errors, setErrors] = useState<ErrorRecord[]>([]);
  const [summary, setSummary] = useState<ErrorSummary | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);

  // Filters
  const [statusTab, setStatusTab] = useState<string>("ALL");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Modals & Drawer
  const [selectedError, setSelectedError] = useState<ErrorRecord | null>(null);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [isResolveModalOpen, setIsResolveModalOpen] = useState(false);
  const [isVerifyModalOpen, setIsVerifyModalOpen] = useState(false);
  const [isReopenModalOpen, setIsReopenModalOpen] = useState(false);

  // Form states
  const [actionErrorTarget, setActionErrorTarget] = useState<ErrorRecord | null>(null);
  const [assigneeName, setAssigneeName] = useState("");
  const [selectedAgentId, setSelectedAgentId] = useState<string>("");
  const [resolutionText, setResolutionText] = useState("");
  const [rootCauseText, setRootCauseText] = useState("");
  const [resolverName, setResolverName] = useState("");
  const [verifierName, setVerifierName] = useState("");
  const [verificationEvidenceText, setVerificationEvidenceText] = useState("");
  const [verifyCloseImmediate, setVerifyCloseImmediate] = useState(false);
  const [reopenReason, setReopenReason] = useState("");
  const [isSubmittingAction, setIsSubmittingAction] = useState(false);

  // Report Error Form State
  const [reportTitle, setReportTitle] = useState("");
  const [reportDesc, setReportDesc] = useState("");
  const [reportSeverity, setReportSeverity] = useState<ErrorSeverity>("MEDIUM");
  const [reportDetector, setReportDetector] = useState("");
  const [reportProjectId, setReportProjectId] = useState("");
  const [reportTaskId, setReportTaskId] = useState("");
  const [reportAssignee, setReportAssignee] = useState("");

  const loadData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setErrorBanner(null);

    try {
      const companies = await api.getCompanies();
      if (!companies || companies.length === 0) {
        setErrorBanner("No active company found. Please create or select a company first.");
        setLoading(false);
        setRefreshing(false);
        return;
      }
      const activeCompany = companies[0];
      setCompany(activeCompany);

      const [errorsRes, summaryRes, projsRes, tasksRes, agentsRes] = await Promise.all([
        api.getCompanyErrors(activeCompany.id, { limit: 100 }),
        api.getCompanyErrorSummary(activeCompany.id),
        api.getProjects(activeCompany.id).catch(() => ({ items: [], total: 0 })),
        api.getTasks(activeCompany.id).catch(() => ({ items: [], total: 0 })),
        api.getAgents(activeCompany.id).catch(() => []),
      ]);

      setErrors(errorsRes.items);
      setSummary(summaryRes);
      setProjects(projsRes.items);
      setTasks(tasksRes.items);
      setAgents(agentsRes);

      // Default detector name
      if (!reportDetector) {
        setReportDetector("operator:lead");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load error and bug telemetry.";
      setErrorBanner(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [reportDetector]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Filtered errors
  const filteredErrors = errors.filter((item) => {
    // Status Tab filter
    if (statusTab === "OPEN" && !["OPEN", "TRIAGED"].includes(item.status)) return false;
    if (statusTab === "ACTIVE" && !["ASSIGNED", "INVESTIGATING", "BLOCKED"].includes(item.status))
      return false;
    if (statusTab === "RESOLVED" && item.status !== "RESOLVED") return false;
    if (statusTab === "VERIFIED" && !["VERIFYING", "VERIFIED", "CLOSED"].includes(item.status))
      return false;

    // Severity filter
    if (severityFilter !== "ALL" && item.severity !== severityFilter) return false;

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = item.title.toLowerCase().includes(q);
      const matchDesc = item.description?.toLowerCase().includes(q) || false;
      const matchDet = item.detected_by.toLowerCase().includes(q);
      const matchAssign = item.assigned_to?.toLowerCase().includes(q) || false;
      const matchProj = item.project_name?.toLowerCase().includes(q) || false;
      if (!matchTitle && !matchDesc && !matchDet && !matchAssign && !matchProj) {
        return false;
      }
    }
    return true;
  });

  // Action handlers
  const handleStartInvestigation = async (errItem: ErrorRecord) => {
    if (!company) return;
    try {
      setRefreshing(true);
      const updated = await api.startErrorInvestigation(company.id, errItem.id, "operator:investigator");
      setErrors((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
      if (selectedError?.id === updated.id) setSelectedError(updated);
      await loadData(true);
    } catch (err: unknown) {
      setErrorBanner(err instanceof Error ? err.message : "Failed to start investigation");
    } finally {
      setRefreshing(false);
    }
  };

  const handleAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!company || !actionErrorTarget || !assigneeName.trim()) return;
    setIsSubmittingAction(true);
    try {
      const updated = await api.assignError(company.id, actionErrorTarget.id, {
        assigned_to: assigneeName.trim(),
        assigned_agent_id: selectedAgentId || undefined,
      });
      setErrors((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
      if (selectedError?.id === updated.id) setSelectedError(updated);
      setIsAssignModalOpen(false);
      setActionErrorTarget(null);
      setAssigneeName("");
      setSelectedAgentId("");
      await loadData(true);
    } catch (err: unknown) {
      setErrorBanner(err instanceof Error ? err.message : "Failed to assign error");
    } finally {
      setIsSubmittingAction(false);
    }
  };

  const handleResolveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!company || !actionErrorTarget || !resolutionText.trim()) return;
    setIsSubmittingAction(true);
    try {
      const updated = await api.resolveError(company.id, actionErrorTarget.id, {
        resolved_by: resolverName.trim() || "operator:lead",
        resolution: resolutionText.trim(),
        root_cause: rootCauseText.trim() || undefined,
        evidence: { resolved_via: "operator_console" },
      });
      setErrors((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
      if (selectedError?.id === updated.id) setSelectedError(updated);
      setIsResolveModalOpen(false);
      setActionErrorTarget(null);
      setResolutionText("");
      setRootCauseText("");
      setResolverName("");
      await loadData(true);
    } catch (err: unknown) {
      setErrorBanner(err instanceof Error ? err.message : "Failed to resolve error");
    } finally {
      setIsSubmittingAction(false);
    }
  };

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!company || !actionErrorTarget) return;
    setIsSubmittingAction(true);
    try {
      let parsedEvidence: Record<string, unknown> = {
        verification_status: "PASSED",
        verified_at: new Date().toISOString(),
      };
      if (verificationEvidenceText.trim()) {
        try {
          parsedEvidence = JSON.parse(verificationEvidenceText);
        } catch {
          parsedEvidence = { notes: verificationEvidenceText.trim() };
        }
      }

      const updated = await api.verifyError(company.id, actionErrorTarget.id, {
        verified_by: verifierName.trim() || "operator:qa",
        evidence: parsedEvidence,
        close_immediately: verifyCloseImmediate,
      });
      setErrors((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
      if (selectedError?.id === updated.id) setSelectedError(updated);
      setIsVerifyModalOpen(false);
      setActionErrorTarget(null);
      setVerifierName("");
      setVerificationEvidenceText("");
      setVerifyCloseImmediate(false);
      await loadData(true);
    } catch (err: unknown) {
      setErrorBanner(err instanceof Error ? err.message : "Failed to verify error");
    } finally {
      setIsSubmittingAction(false);
    }
  };

  const handleReopenSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!company || !actionErrorTarget || !reopenReason.trim()) return;
    setIsSubmittingAction(true);
    try {
      const updated = await api.reopenError(company.id, actionErrorTarget.id, reopenReason.trim());
      setErrors((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
      if (selectedError?.id === updated.id) setSelectedError(updated);
      setIsReopenModalOpen(false);
      setActionErrorTarget(null);
      setReopenReason("");
      await loadData(true);
    } catch (err: unknown) {
      setErrorBanner(err instanceof Error ? err.message : "Failed to reopen error");
    } finally {
      setIsSubmittingAction(false);
    }
  };

  const handleClose = async (errItem: ErrorRecord) => {
    if (!company) return;
    try {
      setRefreshing(true);
      const updated = await api.closeError(company.id, errItem.id);
      setErrors((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
      if (selectedError?.id === updated.id) setSelectedError(updated);
      await loadData(true);
    } catch (err: unknown) {
      setErrorBanner(err instanceof Error ? err.message : "Failed to close error");
    } finally {
      setRefreshing(false);
    }
  };

  const handleCreateErrorSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!company || !reportTitle.trim() || !reportDetector.trim()) return;
    setIsSubmittingAction(true);
    try {
      const payload: ErrorCreatePayload = {
        title: reportTitle.trim(),
        description: reportDesc.trim() || undefined,
        severity: reportSeverity,
        detected_by: reportDetector.trim(),
        project_id: reportProjectId || undefined,
        task_id: reportTaskId || undefined,
        assigned_to: reportAssignee.trim() || undefined,
      };
      const created = await api.createError(company.id, payload);
      setErrors((prev) => [created, ...prev]);
      setIsReportModalOpen(false);
      setReportTitle("");
      setReportDesc("");
      setReportSeverity("MEDIUM");
      setReportProjectId("");
      setReportTaskId("");
      setReportAssignee("");
      await loadData(true);
    } catch (err: unknown) {
      setErrorBanner(err instanceof Error ? err.message : "Failed to record error");
    } finally {
      setIsSubmittingAction(false);
    }
  };

  return (
    <ShellLayout pageTitle="Errors & Bugs" breadcrumb="Error & Bug Management">
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1e2738] pb-5">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
                <Bug className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2.5">
                  Error &amp; Bug Management
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
                    Phase 15
                  </span>
                </h1>
                <p className="text-xs text-slate-400 mt-0.5">
                  Authoritative error lifecycle tracking, root-cause investigation &amp; proof-backed resolution
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={() => loadData(true)}
              disabled={refreshing}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-xs font-medium text-slate-300 hover:text-white border border-slate-700/60 transition shadow-sm"
              title="Refresh error registry"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-indigo-400" : ""}`} />
              Refresh
            </button>

            <button
              onClick={() => setIsReportModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition shadow-sm shadow-indigo-600/30"
            >
              <Bug className="w-3.5 h-3.5" />
              Report Bug / Error
            </button>
          </div>
        </div>

        {/* Error Alert Banner */}
        {errorBanner && (
          <div className="p-3.5 rounded-xl border border-rose-500/30 bg-rose-500/10 flex items-center justify-between text-xs text-rose-300">
            <div className="flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{errorBanner}</span>
            </div>
            <button
              onClick={() => setErrorBanner(null)}
              className="text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Telemetry Metric Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3.5 rounded-xl bg-[#0e131f] border border-[#1e2738] flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Total Errors</span>
              <Bug className="w-3.5 h-3.5 text-slate-500" />
            </div>
            <div className="mt-2 text-2xl font-bold text-white font-mono">
              {summary?.total_errors ?? errors.length}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#0e131f] border border-[#1e2738] flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Open &amp; Triaged</span>
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
            </div>
            <div className="mt-2 text-2xl font-bold text-blue-400 font-mono">
              {(summary?.open_count ?? 0) + (summary?.triaged_count ?? 0)}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#0e131f] border border-[#1e2738] flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Investigating</span>
              <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse"></span>
            </div>
            <div className="mt-2 text-2xl font-bold text-purple-400 font-mono">
              {(summary?.investigating_count ?? 0) + (summary?.assigned_count ?? 0)}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#0e131f] border border-[#1e2738] flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Resolved</span>
              <span className="w-2 h-2 rounded-full bg-teal-400"></span>
            </div>
            <div className="mt-2 text-2xl font-bold text-teal-400 font-mono">
              {summary?.resolved_count ?? 0}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#0e131f] border border-[#1e2738] flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Verified / Closed</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            </div>
            <div className="mt-2 text-2xl font-bold text-emerald-400 font-mono">
              {(summary?.verified_count ?? 0) + (summary?.closed_count ?? 0)}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-rose-500/5 border border-rose-500/25 flex flex-col justify-between">
            <div className="flex items-center justify-between text-rose-400 text-xs font-medium">
              <span>Critical Alerts</span>
              <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
            </div>
            <div className="mt-2 text-2xl font-bold text-rose-400 font-mono">
              {summary?.critical_count ?? 0}
            </div>
          </div>
        </div>

        {/* Filter and Tab Bar */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-[#0e131f] border border-[#1e2738] p-2.5 rounded-xl">
          {/* Status Tabs */}
          <div className="flex items-center gap-1 overflow-x-auto pb-1 md:pb-0">
            {[
              { id: "ALL", label: "All Items" },
              { id: "OPEN", label: "Open & Triaged" },
              { id: "ACTIVE", label: "Investigating" },
              { id: "RESOLVED", label: "Resolved" },
              { id: "VERIFIED", label: "Verified & Closed" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusTab(tab.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition ${
                  statusTab === tab.id
                    ? "bg-indigo-600 text-white shadow-sm shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search & Severity Filter */}
          <div className="flex items-center gap-2">
            <div className="relative flex-1 md:w-56">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search bugs, agents, project..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#111724] border border-[#1e2738] rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-[#111724] border border-[#1e2738] rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>

        {/* Error Items List */}
        {loading ? (
          <div className="h-64 flex flex-col items-center justify-center text-slate-400 gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
            <p className="text-xs">Loading error and bug management records...</p>
          </div>
        ) : filteredErrors.length === 0 ? (
          <div className="h-64 rounded-xl border border-dashed border-[#1e2738] flex flex-col items-center justify-center text-center p-6 text-slate-400">
            <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-3">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-white">No Errors Found</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm">
              {errors.length === 0
                ? "No operational bugs or task errors recorded for this company yet. All execution systems running smoothly."
                : "No error records matched the active tab, severity, or search query filter."}
            </p>
            {errors.length === 0 && (
              <button
                onClick={() => setIsReportModalOpen(true)}
                className="mt-4 px-3.5 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-medium hover:bg-indigo-600/30"
              >
                + Record First Error
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {filteredErrors.map((item) => {
              const sev = SEVERITY_CONFIG[item.severity];
              const st = STATUS_CONFIG[item.status];
              const SevIcon = sev.icon;

              return (
                <div
                  key={item.id}
                  className="p-4 rounded-xl bg-[#0e131f] border border-[#1e2738] hover:border-slate-700/80 transition shadow-sm space-y-3"
                >
                  {/* Card Header */}
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        {/* Severity */}
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold border ${sev.bg} ${sev.text} ${sev.border}`}
                        >
                          <SevIcon className="w-3 h-3" />
                          {sev.label}
                        </span>

                        {/* Status */}
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold border ${st.bg} ${st.text} ${st.border}`}
                        >
                          {st.label}
                        </span>

                        {/* Project / Task Tags */}
                        {item.project_name && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-slate-800/80 text-slate-300 border border-slate-700/60 font-mono">
                            <FolderGit2 className="w-2.5 h-2.5 text-slate-400" />
                            {item.project_name}
                          </span>
                        )}
                        {item.task_title && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-slate-800/80 text-slate-300 border border-slate-700/60 font-mono">
                            <Wrench className="w-2.5 h-2.5 text-slate-400" />
                            {item.task_title}
                          </span>
                        )}
                      </div>

                      <h3 className="text-sm font-semibold text-white tracking-tight truncate">
                        {item.title}
                      </h3>
                      {item.description && (
                        <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                          {item.description}
                        </p>
                      )}
                    </div>

                    {/* Operational Action Buttons */}
                    <div className="flex items-center gap-1.5 shrink-0 self-end sm:self-start">
                      {["OPEN", "TRIAGED"].includes(item.status) && (
                        <button
                          onClick={() => {
                            setActionErrorTarget(item);
                            setAssigneeName(item.assigned_to || "");
                            setIsAssignModalOpen(true);
                          }}
                          className="px-2.5 py-1 rounded bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 border border-indigo-500/30 text-xs font-medium transition"
                        >
                          Assign
                        </button>
                      )}

                      {["ASSIGNED", "OPEN", "TRIAGED"].includes(item.status) && (
                        <button
                          onClick={() => handleStartInvestigation(item)}
                          className="px-2.5 py-1 rounded bg-purple-600/20 text-purple-300 hover:bg-purple-600/30 border border-purple-500/30 text-xs font-medium transition"
                        >
                          Investigate
                        </button>
                      )}

                      {["ASSIGNED", "INVESTIGATING", "BLOCKED"].includes(item.status) && (
                        <button
                          onClick={() => {
                            setActionErrorTarget(item);
                            setResolverName(item.assigned_to || item.investigated_by || "");
                            setIsResolveModalOpen(true);
                          }}
                          className="px-2.5 py-1 rounded bg-teal-600/20 text-teal-300 hover:bg-teal-600/30 border border-teal-500/30 text-xs font-medium transition"
                        >
                          Resolve
                        </button>
                      )}

                      {item.status === "RESOLVED" && (
                        <button
                          onClick={() => {
                            setActionErrorTarget(item);
                            setIsVerifyModalOpen(true);
                          }}
                          className="px-2.5 py-1 rounded bg-emerald-600/20 text-emerald-300 hover:bg-emerald-600/30 border border-emerald-500/30 text-xs font-medium transition"
                        >
                          Verify Proof
                        </button>
                      )}

                      {item.status === "VERIFIED" && (
                        <button
                          onClick={() => handleClose(item)}
                          className="px-2.5 py-1 rounded bg-slate-700/60 text-slate-200 hover:bg-slate-700 border border-slate-600/60 text-xs font-medium transition"
                        >
                          Close
                        </button>
                      )}

                      {["RESOLVED", "VERIFIED", "CLOSED"].includes(item.status) && (
                        <button
                          onClick={() => {
                            setActionErrorTarget(item);
                            setIsReopenModalOpen(true);
                          }}
                          className="px-2.5 py-1 rounded bg-orange-600/20 text-orange-300 hover:bg-orange-600/30 border border-orange-500/30 text-xs font-medium transition"
                          title="Reopen error if recurring"
                        >
                          <RotateCcw className="w-3 h-3 inline mr-1" />
                          Reopen
                        </button>
                      )}

                      <button
                        onClick={() => setSelectedError(item)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-xs font-medium transition inline-flex items-center gap-1"
                      >
                        <Eye className="w-3 h-3" />
                        8-Q Details
                      </button>
                    </div>
                  </div>

                  {/* 8-Questions Fast Reference Strip */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800/80 text-[11px]">
                    <div>
                      <span className="text-slate-500 block text-[10px] uppercase font-mono">
                        Q2: Detected By
                      </span>
                      <span className="text-slate-300 font-medium truncate block">
                        {item.detected_by}
                      </span>
                    </div>

                    <div>
                      <span className="text-slate-500 block text-[10px] uppercase font-mono">
                        Q4: Working On It
                      </span>
                      <span className="text-slate-300 font-medium truncate block">
                        {item.assigned_to || item.assigned_agent_name || "Unassigned"}
                      </span>
                    </div>

                    <div>
                      <span className="text-slate-500 block text-[10px] uppercase font-mono">
                        Q5: Resolved By
                      </span>
                      <span className="text-slate-300 font-medium truncate block">
                        {item.resolved_by || "Pending resolution"}
                      </span>
                    </div>

                    <div>
                      <span className="text-slate-500 block text-[10px] uppercase font-mono">
                        Q6: Verified By
                      </span>
                      <span className="text-slate-300 font-medium truncate block">
                        {item.verified_by || "Pending verification"}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* 8-Questions Detail Drawer Modal */}
        {selectedError && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0c1017] border border-[#1e2738] rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl p-6 space-y-6">
              <div className="flex items-start justify-between border-b border-[#1e2738] pb-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold border ${SEVERITY_CONFIG[selectedError.severity].bg} ${SEVERITY_CONFIG[selectedError.severity].text} ${SEVERITY_CONFIG[selectedError.severity].border}`}
                    >
                      {selectedError.severity}
                    </span>
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold border ${STATUS_CONFIG[selectedError.status].bg} ${STATUS_CONFIG[selectedError.status].text} ${STATUS_CONFIG[selectedError.status].border}`}
                    >
                      {selectedError.status}
                    </span>
                  </div>
                  <h2 className="text-base font-bold text-white">{selectedError.title}</h2>
                </div>
                <button
                  onClick={() => setSelectedError(null)}
                  className="text-slate-400 hover:text-white p-1 rounded-md"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* The 8 Operational Questions Answers */}
              <div className="space-y-4 text-xs">
                {/* Q1 */}
                <div className="p-3 rounded-xl bg-[#111724] border border-[#1e2738] space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400 font-bold block">
                    Q1: What went wrong?
                  </span>
                  <p className="text-slate-200 leading-relaxed font-medium">
                    {selectedError.title}
                  </p>
                  {selectedError.description && (
                    <p className="text-slate-400 leading-relaxed mt-1">
                      {selectedError.description}
                    </p>
                  )}
                </div>

                {/* Q2 */}
                <div className="p-3 rounded-xl bg-[#111724] border border-[#1e2738] space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400 font-bold block">
                    Q2: Who detected it?
                  </span>
                  <p className="text-slate-200">
                    <strong className="text-white">{selectedError.detected_by}</strong> on{" "}
                    {new Date(selectedError.created_at).toLocaleString()}
                  </p>
                </div>

                {/* Q3 */}
                <div className="p-3 rounded-xl bg-[#111724] border border-[#1e2738] space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400 font-bold block">
                    Q3: Who is investigating?
                  </span>
                  <p className="text-slate-200">
                    {selectedError.investigated_by ? (
                      <strong className="text-purple-300">{selectedError.investigated_by}</strong>
                    ) : (
                      <span className="text-slate-500 italic">No investigator assigned yet</span>
                    )}
                  </p>
                </div>

                {/* Q4 */}
                <div className="p-3 rounded-xl bg-[#111724] border border-[#1e2738] space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400 font-bold block">
                    Q4: Who is working on it now?
                  </span>
                  <p className="text-slate-200">
                    {selectedError.assigned_to || selectedError.assigned_agent_name ? (
                      <strong className="text-indigo-300">
                        {selectedError.assigned_to || selectedError.assigned_agent_name}
                      </strong>
                    ) : (
                      <span className="text-slate-500 italic">Unassigned</span>
                    )}
                  </p>
                </div>

                {/* Q5 */}
                <div className="p-3 rounded-xl bg-[#111724] border border-[#1e2738] space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400 font-bold block">
                    Q5: Who resolved it?
                  </span>
                  {selectedError.resolved_by ? (
                    <div className="space-y-1">
                      <p className="text-slate-200">
                        Resolved by <strong className="text-teal-300">{selectedError.resolved_by}</strong>
                        {selectedError.resolved_at && ` at ${new Date(selectedError.resolved_at).toLocaleString()}`}
                      </p>
                      {selectedError.resolution && (
                        <p className="text-slate-300 bg-slate-900/60 p-2 rounded border border-slate-800">
                          {selectedError.resolution}
                        </p>
                      )}
                    </div>
                  ) : (
                    <span className="text-slate-500 italic">Not yet resolved</span>
                  )}
                </div>

                {/* Q6 */}
                <div className="p-3 rounded-xl bg-[#111724] border border-[#1e2738] space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400 font-bold block">
                    Q6: Who verified it?
                  </span>
                  {selectedError.verified_by ? (
                    <p className="text-slate-200">
                      Verified by <strong className="text-emerald-300">{selectedError.verified_by}</strong>
                      {selectedError.verified_at && ` at ${new Date(selectedError.verified_at).toLocaleString()}`}
                    </p>
                  ) : (
                    <span className="text-slate-500 italic">Not yet verified</span>
                  )}
                </div>

                {/* Q7 */}
                <div className="p-3 rounded-xl bg-[#111724] border border-[#1e2738] space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400 font-bold block">
                    Q7: What was the root cause?
                  </span>
                  {selectedError.root_cause ? (
                    <p className="text-slate-200 leading-relaxed font-mono bg-slate-900/60 p-2 rounded border border-slate-800">
                      {selectedError.root_cause}
                    </p>
                  ) : (
                    <span className="text-slate-500 italic">Root cause analysis pending</span>
                  )}
                </div>

                {/* Q8 */}
                <div className="p-3 rounded-xl bg-[#111724] border border-[#1e2738] space-y-1.5">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400 font-bold block">
                    Q8: What evidence proves resolution?
                  </span>
                  {Object.keys(selectedError.evidence || {}).length > 0 ? (
                    <pre className="p-2.5 rounded bg-[#070a10] border border-[#1e2738] text-[11px] font-mono text-emerald-300 overflow-x-auto max-h-48">
                      {JSON.stringify(selectedError.evidence, null, 2)}
                    </pre>
                  ) : (
                    <span className="text-slate-500 italic">No evidence artifact or proof attached</span>
                  )}
                </div>
              </div>

              <div className="flex justify-end pt-2 border-t border-[#1e2738]">
                <button
                  onClick={() => setSelectedError(null)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white"
                >
                  Close Drawer
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Report Error Modal */}
        {isReportModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0c1017] border border-[#1e2738] rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-5">
              <div className="flex items-center justify-between border-b border-[#1e2738] pb-3">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Bug className="w-4 h-4 text-indigo-400" />
                  Report New Error or Bug
                </h3>
                <button
                  onClick={() => setIsReportModalOpen(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleCreateErrorSubmit} className="space-y-4 text-xs">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">
                    Title <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Unhandled NullPointerException in checkout"
                    value={reportTitle}
                    onChange={(e) => setReportTitle(e.target.value)}
                    className="w-full bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">Description</label>
                  <textarea
                    rows={3}
                    placeholder="Details about failure symptoms, expected vs actual behavior..."
                    value={reportDesc}
                    onChange={(e) => setReportDesc(e.target.value)}
                    className="w-full bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Severity</label>
                    <select
                      value={reportSeverity}
                      onChange={(e) => setReportSeverity(e.target.value as ErrorSeverity)}
                      className="w-full bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                    >
                      <option value="CRITICAL">Critical</option>
                      <option value="HIGH">High</option>
                      <option value="MEDIUM">Medium</option>
                      <option value="LOW">Low</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">
                      Detected By <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. operator:lead or agent:QA"
                      value={reportDetector}
                      onChange={(e) => setReportDetector(e.target.value)}
                      className="w-full bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Project (Optional)</label>
                    <select
                      value={reportProjectId}
                      onChange={(e) => setReportProjectId(e.target.value)}
                      className="w-full bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                    >
                      <option value="">None</option>
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Task (Optional)</label>
                    <select
                      value={reportTaskId}
                      onChange={(e) => setReportTaskId(e.target.value)}
                      className="w-full bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                    >
                      <option value="">None</option>
                      {tasks.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.title}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">Assign To (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. agent:Coder or name"
                    value={reportAssignee}
                    onChange={(e) => setReportAssignee(e.target.value)}
                    className="w-full bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-[#1e2738]">
                  <button
                    type="button"
                    onClick={() => setIsReportModalOpen(false)}
                    className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmittingAction}
                    className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold flex items-center gap-1.5"
                  >
                    {isSubmittingAction && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    Record Error
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Assign Modal */}
        {isAssignModalOpen && actionErrorTarget && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0c1017] border border-[#1e2738] rounded-2xl w-full max-w-md shadow-2xl p-6 space-y-5">
              <div className="flex items-center justify-between border-b border-[#1e2738] pb-3">
                <h3 className="text-base font-bold text-white">Assign Error</h3>
                <button
                  onClick={() => setIsAssignModalOpen(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleAssignSubmit} className="space-y-4 text-xs">
                <p className="text-slate-300 font-medium">
                  Error: <strong className="text-white">{actionErrorTarget.title}</strong>
                </p>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">Select Registered Agent</label>
                  <select
                    value={selectedAgentId}
                    onChange={(e) => {
                      const aId = e.target.value;
                      setSelectedAgentId(aId);
                      const ag = agents.find((a) => a.id === aId);
                      if (ag) setAssigneeName(ag.name);
                    }}
                    className="w-full bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">Custom Assignee Name...</option>
                    {agents.map((ag) => (
                      <option key={ag.id} value={ag.id}>
                        {ag.name} ({ag.role})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">
                    Assignee Name / Identifier <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Coder Agent or User"
                    value={assigneeName}
                    onChange={(e) => setAssigneeName(e.target.value)}
                    className="w-full bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-[#1e2738]">
                  <button
                    type="button"
                    onClick={() => setIsAssignModalOpen(false)}
                    className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmittingAction || !assigneeName.trim()}
                    className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold flex items-center gap-1.5"
                  >
                    {isSubmittingAction && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    Confirm Assignment
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Resolve Modal */}
        {isResolveModalOpen && actionErrorTarget && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0c1017] border border-[#1e2738] rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-5">
              <div className="flex items-center justify-between border-b border-[#1e2738] pb-3">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-teal-400" />
                  Mark Error Resolved
                </h3>
                <button
                  onClick={() => setIsResolveModalOpen(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleResolveSubmit} className="space-y-4 text-xs">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">
                    Resolved By <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Coder Agent"
                    value={resolverName}
                    onChange={(e) => setResolverName(e.target.value)}
                    className="w-full bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">
                    Resolution Description <span className="text-rose-400">*</span>
                  </label>
                  <textarea
                    rows={3}
                    required
                    placeholder="Describe exactly what code changes, fixes, or configurations resolved this bug..."
                    value={resolutionText}
                    onChange={(e) => setResolutionText(e.target.value)}
                    className="w-full bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">Root Cause Analysis</label>
                  <textarea
                    rows={2}
                    placeholder="Why did this bug occur in the first place? (e.g. unhandled edge case in parse logic)"
                    value={rootCauseText}
                    onChange={(e) => setRootCauseText(e.target.value)}
                    className="w-full bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-[#1e2738]">
                  <button
                    type="button"
                    onClick={() => setIsResolveModalOpen(false)}
                    className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmittingAction || !resolutionText.trim()}
                    className="px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-semibold flex items-center gap-1.5"
                  >
                    {isSubmittingAction && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    Confirm Resolution
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Verify Modal */}
        {isVerifyModalOpen && actionErrorTarget && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0c1017] border border-[#1e2738] rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-5">
              <div className="flex items-center justify-between border-b border-[#1e2738] pb-3">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <FileCheck2 className="w-4 h-4 text-emerald-400" />
                  Verify Resolution Evidence
                </h3>
                <button
                  onClick={() => setIsVerifyModalOpen(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleVerifySubmit} className="space-y-4 text-xs">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">
                    Verified By <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. QA Auditor or operator:auditor"
                    value={verifierName}
                    onChange={(e) => setVerifierName(e.target.value)}
                    className="w-full bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">
                    Evidence / Proof of Fix (JSON or Verification Notes) <span className="text-rose-400">*</span>
                  </label>
                  <textarea
                    rows={4}
                    required
                    placeholder='{"automated_test": "PASSED", "commit_hash": "a1b2c3d", "verification_run_id": "tr-102"}'
                    value={verificationEvidenceText}
                    onChange={(e) => setVerificationEvidenceText(e.target.value)}
                    className="w-full font-mono bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                  <p className="text-[11px] text-slate-500 mt-1">
                    Per Phase 15 specification, verified errors require concrete test/output evidence proving the fix.
                  </p>
                </div>

                <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={verifyCloseImmediate}
                    onChange={(e) => setVerifyCloseImmediate(e.target.checked)}
                    className="rounded bg-[#111724] border-[#1e2738] text-indigo-600 focus:ring-0"
                  />
                  <span>Close error immediately upon verification</span>
                </label>

                <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-[#1e2738]">
                  <button
                    type="button"
                    onClick={() => setIsVerifyModalOpen(false)}
                    className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmittingAction || !verifierName.trim()}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center gap-1.5"
                  >
                    {isSubmittingAction && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    Confirm Verification
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Reopen Modal */}
        {isReopenModalOpen && actionErrorTarget && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0c1017] border border-[#1e2738] rounded-2xl w-full max-w-md shadow-2xl p-6 space-y-5">
              <div className="flex items-center justify-between border-b border-[#1e2738] pb-3">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <RotateCcw className="w-4 h-4 text-orange-400" />
                  Reopen Error
                </h3>
                <button
                  onClick={() => setIsReopenModalOpen(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleReopenSubmit} className="space-y-4 text-xs">
                <p className="text-slate-300 font-medium">
                  Error: <strong className="text-white">{actionErrorTarget.title}</strong>
                </p>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">
                    Reason for Reopening <span className="text-rose-400">*</span>
                  </label>
                  <textarea
                    rows={3}
                    required
                    placeholder="Describe how the bug reappeared or why verification failed..."
                    value={reopenReason}
                    onChange={(e) => setReopenReason(e.target.value)}
                    className="w-full bg-[#111724] border border-[#1e2738] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-[#1e2738]">
                  <button
                    type="button"
                    onClick={() => setIsReopenModalOpen(false)}
                    className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmittingAction || !reopenReason.trim()}
                    className="px-4 py-2 rounded-lg bg-orange-600 hover:bg-orange-500 text-white font-semibold flex items-center gap-1.5"
                  >
                    {isSubmittingAction && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    Confirm Reopen
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
