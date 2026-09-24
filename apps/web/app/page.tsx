"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bot,
  Bug,
  Building2,
  CheckCircle2,
  CheckSquare,
  Database,
  FolderGit2,
  Lock,
  RefreshCw,
  Server,
  ShieldAlert,
  User as UserIcon,
  Users,
} from "lucide-react";
import Link from "next/link";
import {
  api,
  Company,
  SystemStatus,
  User,
  ActivityEvent,
  AgentPresence,
  ErrorSummary,
  PresenceSummary,
} from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins < 60) return `${mins}m ${secs}s`;
  const hours = Math.floor(mins / 60);
  return `${hours}h ${mins % 60}m`;
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffSec < 5) return "just now";
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export default function DashboardPage() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [activeCompany, setActiveCompany] = useState<Company | null>(null);
  const [departmentCount, setDepartmentCount] = useState<number>(0);
  const [agentCount, setAgentCount] = useState<number>(0);
  const [planCount, setPlanCount] = useState<number>(0);
  const [hasCeo, setHasCeo] = useState<boolean>(false);
  const [projectCount, setProjectCount] = useState<number>(0);
  const [openTaskCount, setOpenTaskCount] = useState<number>(0);
  const [blockedTaskCount, setBlockedTaskCount] = useState<number>(0);
  const [pendingApprovalCount, setPendingApprovalCount] = useState<number>(0);
  const [decisionCount, setDecisionCount] = useState<number>(0);
  const [recentActivity, setRecentActivity] = useState<ActivityEvent[]>([]);
  const [presenceSummary, setPresenceSummary] = useState<PresenceSummary | null>(null);
  const [activePresences, setActivePresences] = useState<AgentPresence[]>([]);
  const [errorSummary, setErrorSummary] = useState<ErrorSummary | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>("");

  async function loadTelemetry() {
    setStatusLoading(true);
    try {
      const [user, status, companies] = await Promise.all([
        api.getMe(),
        api.getSystemStatus(),
        api.getCompanies().catch(() => [] as Company[]),
      ]);
      setCurrentUser(user);
      setSystemStatus(status);
      const primaryCompany = companies[0] || null;
      setActiveCompany(primaryCompany);
      if (primaryCompany) {
        try {
          const [depts, ags, plns, ctx, projs, tsks, apprs, decs, acts, presSumm, presList, errSumm] =
            await Promise.all([
              api.getDepartments(primaryCompany.id).catch(() => []),
              api.getAgents(primaryCompany.id).catch(() => []),
              api.getPlans(primaryCompany.id).catch(() => []),
              api.getCeoContext(primaryCompany.id).catch(() => null),
              api.getProjects(primaryCompany.id).catch(() => ({ items: [], total: 0 })),
              api.getTasks(primaryCompany.id).catch(() => ({ items: [], total: 0 })),
              api
                .getApprovals(primaryCompany.id, { status: "PENDING" })
                .catch(() => ({ items: [], total: 0 })),
              api.getCompanyDecisions(primaryCompany.id).catch(() => ({ items: [], total: 0 })),
              api.getActivity(primaryCompany.id, { limit: 5 }).catch(() => ({ items: [], total: 0 })),
              api.getPresenceSummary(primaryCompany.id).catch(() => null),
              api.getCompanyPresence(primaryCompany.id).catch(() => ({ items: [], total: 0 })),
              api.getCompanyErrorSummary(primaryCompany.id).catch(() => null),
            ]);
          setDepartmentCount(depts.length);
          setAgentCount(ags.length);
          setPlanCount(plns.length);
          setHasCeo(!!ctx?.ceo_agent);
          setProjectCount(projs.total);
          const open = tsks.items.filter((t) => t.status !== "COMPLETED" && t.status !== "CANCELLED");
          const blocked = tsks.items.filter((t) => t.status === "BLOCKED");
          setOpenTaskCount(open.length);
          setBlockedTaskCount(blocked.length);
          setPendingApprovalCount(apprs.total);
          setDecisionCount(decs.total);
          setRecentActivity(acts.items);
          setPresenceSummary(presSumm);
          setActivePresences(presList.items);
          setErrorSummary(errSumm);
        } catch {
          setDepartmentCount(0);
          setAgentCount(0);
          setPlanCount(0);
          setHasCeo(false);
          setProjectCount(0);
          setOpenTaskCount(0);
          setBlockedTaskCount(0);
          setPendingApprovalCount(0);
          setDecisionCount(0);
          setRecentActivity([]);
          setPresenceSummary(null);
          setActivePresences([]);
          setErrorSummary(null);
        }
      } else {
        setDepartmentCount(0);
        setAgentCount(0);
        setPlanCount(0);
        setHasCeo(false);
        setProjectCount(0);
        setOpenTaskCount(0);
        setBlockedTaskCount(0);
        setPendingApprovalCount(0);
        setDecisionCount(0);
        setRecentActivity([]);
        setPresenceSummary(null);
        setActivePresences([]);
        setErrorSummary(null);
      }
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch {
      // Telemetry will fall back gracefully
    } finally {
      setStatusLoading(false);
    }
  }

  useEffect(() => {
    loadTelemetry();
  }, []);

  const metricCards = [
    {
      title: "Active Projects",
      value: projectCount.toString(),
      subtext: projectCount > 0 ? `${projectCount} active projects in portfolio` : "No active projects",
      phaseNote: "Phase 12 Kanban Active",
      icon: FolderGit2,
      accentColor: "text-blue-400",
      bgColor: "bg-blue-500/10",
      borderColor: "border-blue-500/20",
    },
    {
      title: "Open Tasks",
      value: openTaskCount.toString(),
      subtext: openTaskCount > 0 ? `${openTaskCount} tasks in execution pipeline` : "No open tasks",
      phaseNote: "Phase 12 Kanban Active",
      icon: CheckSquare,
      accentColor: "text-indigo-400",
      bgColor: "bg-indigo-500/10",
      borderColor: "border-indigo-500/20",
    },
    {
      title: "Blocked Tasks",
      value: blockedTaskCount.toString(),
      subtext: blockedTaskCount > 0 ? `${blockedTaskCount} tasks blocked on dependencies` : "0 blocked tasks",
      phaseNote: "Operational baseline",
      icon: AlertTriangle,
      accentColor: "text-amber-400",
      bgColor: "bg-amber-500/10",
      borderColor: "border-amber-500/20",
    },
    {
      title: "Pending Approvals",
      value: pendingApprovalCount.toString(),
      subtext:
        pendingApprovalCount > 0
          ? `${pendingApprovalCount} actions require human sign-off`
          : "0 pending approvals",
      phaseNote: "Phase 10 Active",
      icon: ShieldAlert,
      accentColor: pendingApprovalCount > 0 ? "text-rose-400" : "text-amber-400",
      bgColor: pendingApprovalCount > 0 ? "bg-rose-500/10" : "bg-amber-500/10",
      borderColor: pendingApprovalCount > 0 ? "border-rose-500/30" : "border-amber-500/20",
    },
    {
      title: "Active Agents",
      value: presenceSummary ? presenceSummary.working_count.toString() : "0",
      subtext:
        presenceSummary && presenceSummary.working_count > 0
          ? `${presenceSummary.working_count} active (${presenceSummary.idle_count} idle)`
          : agentCount > 0
          ? `${agentCount} registered (all idle)`
          : "No active agents",
      phaseNote: "Phase 14 Presence Active",
      icon: Users,
      accentColor:
        presenceSummary && presenceSummary.working_count > 0
          ? "text-emerald-400"
          : "text-slate-400",
      bgColor:
        presenceSummary && presenceSummary.working_count > 0
          ? "bg-emerald-500/10"
          : "bg-slate-800/40",
      borderColor:
        presenceSummary && presenceSummary.working_count > 0
          ? "border-emerald-500/20"
          : "border-slate-700/40",
    },
    {
      title: "Errors & Bugs",
      value: errorSummary
        ? (errorSummary.open_count + errorSummary.investigating_count + errorSummary.assigned_count).toString()
        : "0",
      subtext:
        errorSummary && errorSummary.critical_count > 0
          ? `${errorSummary.critical_count} critical alerts requiring action`
          : "0 critical bugs",
      phaseNote: "Phase 15 Error Console",
      icon: Bug,
      accentColor:
        errorSummary && errorSummary.critical_count > 0
          ? "text-rose-400"
          : errorSummary && (errorSummary.open_count + errorSummary.investigating_count) > 0
          ? "text-amber-400"
          : "text-slate-400",
      bgColor:
        errorSummary && errorSummary.critical_count > 0
          ? "bg-rose-500/10"
          : errorSummary && (errorSummary.open_count + errorSummary.investigating_count) > 0
          ? "bg-amber-500/10"
          : "bg-slate-800/40",
      borderColor:
        errorSummary && errorSummary.critical_count > 0
          ? "border-rose-500/25"
          : errorSummary && (errorSummary.open_count + errorSummary.investigating_count) > 0
          ? "border-amber-500/20"
          : "border-slate-700/40",
    },
  ];

  return (
    <ShellLayout pageTitle="Dashboard" breadcrumb="Executive Control">
      <div className="space-y-8">
        {/* Executive Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-[#1e2738]">
          <div>
            <div className="flex flex-wrap items-center gap-3 mb-1">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                {activeCompany ? activeCompany.name : "Executive Dashboard"}
              </h1>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                {systemStatus?.current_phase || "Phase 12 Active"}
              </span>
              {activeCompany?.industry && (
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  {activeCompany.industry}
                </span>
              )}
            </div>
            <p className="text-xs sm:text-sm text-slate-400">
              {activeCompany?.mission || activeCompany?.description || "Real-time operating picture of company systems, foundation, and agent readiness."}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadTelemetry}
              disabled={statusLoading}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[#1e2738] bg-[#111724] hover:bg-[#182030] text-xs font-medium text-slate-300 hover:text-white transition disabled:opacity-50"
              aria-label="Refresh telemetry"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${statusLoading ? "animate-spin text-indigo-400" : ""}`} />
              <span>Refresh Telemetry</span>
            </button>
            {lastRefreshed && (
              <span className="text-[11px] font-mono text-slate-400 hidden md:inline">
                Synced at {lastRefreshed}
              </span>
            )}
          </div>
        </div>

        {/* Company Provisioning Notice if No Company Exists */}
        {!statusLoading && !activeCompany && (
          <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/5 p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-white">No Company Provisioned</h4>
                <p className="text-xs text-slate-400">
                  Establish your company identity and organizational departments to activate company-scoped operations.
                </p>
              </div>
            </div>
            <Link
              href="/company"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white transition"
            >
              <span>Setup Company</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        )}

        {/* Top Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {metricCards.map((card) => {
            const Icon = card.icon;
            return (
              <div
                key={card.title}
                className="rounded-xl border border-[#1e2738] bg-[#111724] p-5 flex flex-col justify-between hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-medium text-slate-400">{card.title}</span>
                  <div className={`p-2 rounded-lg ${card.bgColor} ${card.accentColor} border ${card.borderColor}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-white font-mono tracking-tight mb-1">
                    {card.value}
                  </div>
                  <div className="text-xs text-slate-400 truncate">{card.subtext}</div>
                  <div className="text-[10px] text-slate-400 mt-2 pt-2 border-t border-[#1e2738]/60 font-mono">
                    {card.phaseNote}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Operational Panels Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Active Operations Panel */}
          <div className="rounded-xl border border-[#1e2738] bg-[#111724] p-6 flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-[#1e2738] mb-6">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">Active Operations</h3>
                  <p className="text-xs text-slate-400">CEO coordination and multi-agent execution</p>
                </div>
              </div>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Phase 8 Active
              </span>
            </div>

            {/* Phase 5 State */}
            <div className="flex-1 flex flex-col items-center justify-center text-center py-6 px-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4">
                <Bot className="w-6 h-6" />
              </div>
              <h4 className="text-sm font-semibold text-white mb-1">
                {planCount > 0
                  ? "CEO Planning Active"
                  : hasCeo
                  ? "CEO Orchestrator Configured"
                  : "CEO Agent Required"}
              </h4>
              <p className="text-xs text-slate-400 max-w-sm leading-relaxed mb-4">
                {planCount > 0
                  ? `${planCount} strategic plan proposals synthesized by the CEO. All plans remain in PROPOSAL state awaiting governance approval.`
                  : hasCeo
                  ? "The CEO agent is registered and ready to intake goals, formulate task graph DAGs, and structure delegation proposals."
                  : "Register or provision a CEO agent in the Agent Registry to begin strategic goal intake and planning."}
              </p>
              <Link
                href={hasCeo ? "/ceo" : "/agents"}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-black font-semibold text-xs hover:bg-primary/90 transition-colors"
              >
                <span>{hasCeo ? "Open CEO Command Center" : "Provision CEO Agent"}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Recent Activity Panel */}
          <div className="rounded-xl border border-[#1e2738] bg-[#111724] p-6 flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-[#1e2738] mb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <Activity className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">Recent Activity</h3>
                  <p className="text-xs text-slate-400">Operational timeline and event feed</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Phase 13 Active
                </span>
              </div>
            </div>

            {recentActivity.length > 0 ? (
              <div className="flex-1 flex flex-col justify-between">
                <div className="space-y-3">
                  {recentActivity.map((event) => {
                    const isAgent = event.actor_type === "AGENT";
                    const isOperator = event.actor_type === "USER";
                    return (
                      <div
                        key={event.id}
                        className="p-3 rounded-lg bg-[#0c1017] border border-[#1e2738] hover:border-slate-700/80 transition-colors flex items-start gap-3 text-xs"
                      >
                        <div className="mt-0.5 shrink-0">
                          {isAgent ? (
                            <div className="p-1.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                              <Bot className="w-3.5 h-3.5" />
                            </div>
                          ) : isOperator ? (
                            <div className="p-1.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                              <UserIcon className="w-3.5 h-3.5" />
                            </div>
                          ) : (
                            <div className="p-1.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                              <Activity className="w-3.5 h-3.5" />
                            </div>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 truncate">
                              {event.event_type.replace(/_/g, " ")}
                            </span>
                            <span className="text-[10px] font-mono text-slate-400 shrink-0">
                              {formatRelativeTime(event.created_at)}
                            </span>
                          </div>
                          <p className="text-slate-200 text-xs line-clamp-2 leading-relaxed font-normal">
                            {event.message}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="pt-4 mt-2 border-t border-[#1e2738]/60 flex justify-end">
                  <Link
                    href="/activity"
                    className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
                  >
                    <span>View full company activity</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center py-8 px-4">
                <div className="w-12 h-12 rounded-xl bg-slate-800/60 border border-slate-700/60 text-slate-400 flex items-center justify-center mb-4">
                  <Activity className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-semibold text-white mb-1">
                  No Activity Recorded Yet
                </h4>
                <p className="text-xs text-slate-400 max-w-sm leading-relaxed mb-4">
                  Operational company events will appear here as projects, tasks, approvals, and decisions are created or updated.
                </p>
                <Link
                  href="/activity"
                  className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg border border-[#1e2738] bg-[#0c1017] hover:bg-[#182030] text-xs font-medium text-slate-300 hover:text-white transition"
                >
                  <span>Open Activity Console</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Who is working now? Panel per docs/Phases.md § 18 */}
        <div className="rounded-xl border border-[#1e2738] bg-[#111724] p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-4 border-b border-[#1e2738] mb-6">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <Users className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-white">Who is working now?</h3>
                  {presenceSummary && presenceSummary.working_count > 0 && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                      {presenceSummary.working_count} Active
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400">
                  Real-time agent presence, active task execution, and operational focus
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                Phase 14 Active
              </span>
              <Link
                href="/agents"
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1 transition"
              >
                <span>Agent Registry</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {activePresences.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {activePresences.map((presence) => {
                const isWorking = presence.status === "WORKING";
                const isIdle = presence.status === "IDLE";
                const isWaiting = presence.status === "WAITING";
                const isBlocked = presence.status === "BLOCKED";
                const isError = presence.status === "ERROR";

                const badgeBg = isWorking
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                  : isWaiting
                  ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                  : isBlocked
                  ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                  : isError
                  ? "bg-red-500/10 text-red-400 border-red-500/30"
                  : "bg-slate-800 text-slate-400 border-slate-700";

                return (
                  <div
                    key={presence.id}
                    className={`p-4 rounded-xl border transition-all ${
                      isWorking
                        ? "bg-[#0d141e] border-emerald-500/30 shadow-sm"
                        : "bg-[#0c1017] border-[#1e2738] hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div
                          className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border ${
                            isWorking
                              ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-400"
                              : "bg-slate-800 border-slate-700 text-slate-400"
                          }`}
                        >
                          <Bot className="w-4 h-4" />
                        </div>
                        <div className="min-w-0">
                          <h4 className="text-xs font-semibold text-white truncate">
                            {presence.agent_name}
                          </h4>
                          <p className="text-[11px] text-slate-400 truncate">
                            {presence.agent_role}
                          </p>
                        </div>
                      </div>

                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono border shrink-0 ${badgeBg}`}
                      >
                        {isWorking && (
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                        )}
                        <span>{presence.status}</span>
                      </span>
                    </div>

                    <div className="mt-3 pt-3 border-t border-[#1e2738]/60 space-y-1.5 text-xs">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-slate-400 font-medium">Activity:</span>
                        <span className="text-slate-200 font-medium truncate max-w-[180px]">
                          {presence.current_activity || (isIdle ? "Idle · Awaiting Task" : "Standby")}
                        </span>
                      </div>

                      {presence.current_task_title && (
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-400 font-medium">Task:</span>
                          <span className="text-indigo-400 truncate max-w-[180px]" title={presence.current_task_title}>
                            {presence.current_task_title}
                          </span>
                        </div>
                      )}

                      {isWorking && presence.duration_seconds > 0 && (
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-400 font-medium">Active Duration:</span>
                          <span className="font-mono text-emerald-400">
                            {formatDuration(presence.duration_seconds)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center text-center py-8 px-4">
              <div className="w-12 h-12 rounded-xl bg-slate-800/60 border border-slate-700/60 text-slate-400 flex items-center justify-center mb-3">
                <Users className="w-6 h-6" />
              </div>
              <h4 className="text-sm font-semibold text-white mb-1">
                No Agents Registered
              </h4>
              <p className="text-xs text-slate-400 max-w-sm mb-4">
                Register specialist agents in the Agent Registry to monitor real-time execution presence.
              </p>
              <Link
                href="/agents"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white transition"
              >
                <span>Register Agent</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}
        </div>

        {/* Live System Readiness & Telemetry Panel */}
        <div className="rounded-xl border border-[#1e2738] bg-[#111724] p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-4 border-b border-[#1e2738] mb-6">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Server className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">
                  System Foundation & Infrastructure Telemetry
                </h3>
                <p className="text-xs text-slate-400">
                  Verified real-time operational status from backend services and PostgreSQL
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>Authoritative State Active</span>
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* PostgreSQL Telemetry */}
            <div className="p-4 rounded-lg bg-[#0c1017] border border-[#1e2738]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400 font-medium">Core Database</span>
                <Database className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-sm font-semibold text-white mb-1 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>PostgreSQL 16</span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                Status: {systemStatus?.database === "connected" ? "Connected (SELECT 1 OK)" : "Degraded"}
              </p>
            </div>

            {/* Auth Authority Telemetry */}
            <div className="p-4 rounded-lg bg-[#0c1017] border border-[#1e2738]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400 font-medium">Session Authority</span>
                <Lock className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-sm font-semibold text-white mb-1 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>PostgreSQL Sessions</span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                Operator: {currentUser?.email || "verified"}
              </p>
            </div>

            {/* API Service Telemetry */}
            <div className="p-4 rounded-lg bg-[#0c1017] border border-[#1e2738]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400 font-medium">FastAPI Backend</span>
                <Server className="w-4 h-4 text-blue-400" />
              </div>
              <div className="text-sm font-semibold text-white mb-1 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>API Gateway v{systemStatus?.version || "0.1.0"}</span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                Env: {systemStatus?.environment || "development"}
              </p>
            </div>

            {/* Roadmap & Organization Status */}
            <div className="p-4 rounded-lg bg-[#0c1017] border border-[#1e2738]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400 font-medium">Organization State</span>
                <Building2 className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-sm font-semibold text-white mb-1 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span className="truncate">{activeCompany ? activeCompany.name : "Unassigned"}</span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                {activeCompany ? `${departmentCount} Depts · ${agentCount} Agents · ${decisionCount} Decisions` : "Phase 11 Active"}
              </p>
            </div>
          </div>
        </div>
      </div>
    </ShellLayout>
  );
}
