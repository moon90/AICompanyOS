"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  Activity,
  AlertCircle,
  ArrowRight,
  Bot,
  Brain,
  Building2,
  Calendar,
  CheckCircle2,
  CheckSquare,
  Clock,
  ExternalLink,
  Eye,
  Filter,
  FolderGit2,
  Layers,
  Loader2,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
  User as UserIcon,
  Users,
  Wrench,
  X,
  Zap,
} from "lucide-react";
import Link from "next/link";
import {
  ActivityEvent,
  Agent,
  api,
  Company,
  Project,
  Task,
} from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

type ScopeType = "company" | "project" | "task" | "agent";

const EVENT_TYPE_CATEGORIES: Record<
  string,
  { label: string; bg: string; text: string; border: string; icon: React.ComponentType<{ className?: string }> }
> = {
  PROJECT_CREATED: {
    label: "Project Created",
    bg: "bg-blue-500/10",
    text: "text-blue-400",
    border: "border-blue-500/20",
    icon: FolderGit2,
  },
  PROJECT_STATUS_CHANGED: {
    label: "Project Transition",
    bg: "bg-blue-500/10",
    text: "text-blue-400",
    border: "border-blue-500/20",
    icon: FolderGit2,
  },
  TASK_CREATED: {
    label: "Task Created",
    bg: "bg-indigo-500/10",
    text: "text-indigo-400",
    border: "border-indigo-500/20",
    icon: CheckSquare,
  },
  TASK_ASSIGNED: {
    label: "Task Assigned",
    bg: "bg-cyan-500/10",
    text: "text-cyan-400",
    border: "border-cyan-500/20",
    icon: Users,
  },
  TASK_STATUS_CHANGED: {
    label: "Task Transition",
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/20",
    icon: ArrowRight,
  },
  TASK_DELEGATED: {
    label: "Delegation",
    bg: "bg-purple-500/10",
    text: "text-purple-400",
    border: "border-purple-500/20",
    icon: Bot,
  },
  EXECUTION_STARTED: {
    label: "Run Started",
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/20",
    icon: Zap,
  },
  EXECUTION_COMPLETED: {
    label: "Run Completed",
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/20",
    icon: CheckCircle2,
  },
  TASK_FAILED: {
    label: "Task Failed",
    bg: "bg-rose-500/10",
    text: "text-rose-400",
    border: "border-rose-500/20",
    icon: AlertCircle,
  },
  TASK_RECOVERED: {
    label: "Task Recovered",
    bg: "bg-teal-500/10",
    text: "text-teal-400",
    border: "border-teal-500/20",
    icon: CheckCircle2,
  },
  APPROVAL_REQUESTED: {
    label: "Approval Needed",
    bg: "bg-rose-500/10",
    text: "text-rose-400",
    border: "border-rose-500/20",
    icon: ShieldAlert,
  },
  APPROVAL_RESOLVED: {
    label: "Approval Decision",
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/20",
    icon: ShieldAlert,
  },
  DECISION_RECORDED: {
    label: "Decision Recorded",
    bg: "bg-purple-500/10",
    text: "text-purple-400",
    border: "border-purple-500/20",
    icon: Brain,
  },
  DECISION_SUPERSEDED: {
    label: "Decision Superseded",
    bg: "bg-indigo-500/10",
    text: "text-indigo-400",
    border: "border-indigo-500/20",
    icon: Brain,
  },
  TOOL_EXECUTED: {
    label: "Tool Run",
    bg: "bg-cyan-500/10",
    text: "text-cyan-400",
    border: "border-cyan-500/20",
    icon: Wrench,
  },
};

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

export default function ActivityPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [activeCompany, setActiveCompany] = useState<Company | null>(null);

  // Companion datasets for selectors
  const [projects, setProjects] = useState<Project[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);

  // Filtering state
  const [scope, setScope] = useState<ScopeType>("company");
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [selectedTaskId, setSelectedTaskId] = useState<string>("");
  const [selectedAgentId, setSelectedAgentId] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Events & Pagination
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [totalEvents, setTotalEvents] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Live Auto-Refresh (every 12 seconds)
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>("");

  // Inspect metadata modal
  const [inspectEvent, setInspectEvent] = useState<ActivityEvent | null>(null);

  // 1. Initial Load of Companies
  useEffect(() => {
    async function init() {
      try {
        const comps = await api.getCompanies();
        setCompanies(comps);
        if (comps.length > 0) {
          setActiveCompany(comps[0]);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load company context");
      }
    }
    init();
  }, []);

  // 2. Load companion resources when activeCompany changes
  useEffect(() => {
    if (!activeCompany) return;
    async function loadResources() {
      try {
        const [projRes, agRes] = await Promise.all([
          api.getProjects(activeCompany!.id, { limit: 100 }).catch(() => ({ items: [], total: 0 })),
          api.getAgents(activeCompany!.id).catch(() => [] as Agent[]),
        ]);
        setProjects(projRes.items);
        setAgents(agRes);
      } catch {
        // Fall back gracefully
      }
    }
    loadResources();
  }, [activeCompany]);

  // 3. Fetch Activity Events
  const fetchActivity = useCallback(async () => {
    if (!activeCompany) return;
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = {
        limit: 100,
        offset: 0,
      };

      if (searchQuery.trim()) {
        params.search = searchQuery.trim();
      }

      if (categoryFilter !== "ALL") {
        params.event_type = categoryFilter;
      }

      let res;
      if (scope === "project" && selectedProjectId) {
        res = await api.getProjectActivity(activeCompany.id, selectedProjectId, params);
      } else if (scope === "task" && selectedTaskId.trim()) {
        res = await api.getTaskActivity(activeCompany.id, selectedTaskId.trim(), params);
      } else if (scope === "agent" && selectedAgentId) {
        res = await api.getAgentActivity(activeCompany.id, selectedAgentId, params);
      } else {
        res = await api.getActivity(activeCompany.id, params);
      }

      setEvents(res.items);
      setTotalEvents(res.total);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load activity stream");
    } finally {
      setLoading(false);
    }
  }, [activeCompany, scope, selectedProjectId, selectedTaskId, selectedAgentId, categoryFilter, searchQuery]);

  useEffect(() => {
    fetchActivity();
  }, [fetchActivity]);

  // 4. Periodic auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchActivity();
    }, 12000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchActivity]);

  return (
    <ShellLayout pageTitle="Activity" breadcrumb="System & Governance">
      <div className="space-y-6 pb-12">
        {/* Top Header */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-[#111724] p-5 rounded-xl border border-[#1e2738]">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Activity className="w-5 h-5" />
              </div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                Operational Activity Stream
              </h1>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Phase 13 Active
              </span>
            </div>
            <p className="text-xs text-slate-400 max-w-2xl">
              Human-readable timeline of decisions, project milestones, task state transitions, agent executions, and approvals across the company.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {companies.length > 1 && (
              <select
                value={activeCompany?.id || ""}
                onChange={(e) => {
                  const c = companies.find((comp) => comp.id === e.target.value);
                  if (c) setActiveCompany(c);
                }}
                className="bg-[#0c1017] border border-[#1e2738] text-xs text-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
              >
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            )}

            {/* Auto-Refresh Toggle */}
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition ${
                autoRefresh
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                  : "bg-[#0c1017] border-[#1e2738] text-slate-400 hover:text-white"
              }`}
              title={autoRefresh ? "Auto-refreshing every 12s" : "Auto-refresh paused"}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  autoRefresh ? "bg-emerald-400 animate-pulse" : "bg-slate-500"
                }`}
              />
              <span>Live Stream</span>
            </button>

            {/* Manual Refresh */}
            <button
              onClick={() => fetchActivity()}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center justify-between text-rose-400 text-xs">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="hover:text-rose-300">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Scope Navigation & Filter Bar */}
        <div className="bg-[#111724] border border-[#1e2738] rounded-xl p-4 space-y-4">
          {/* Scope Tabs */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#1e2738] pb-3">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mr-2">
                Scope:
              </span>
              <button
                onClick={() => {
                  setScope("company");
                  setSelectedProjectId("");
                  setSelectedTaskId("");
                  setSelectedAgentId("");
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  scope === "company"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/60"
                }`}
              >
                All Company
              </button>
              <button
                onClick={() => setScope("project")}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  scope === "project"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/60"
                }`}
              >
                By Project
              </button>
              <button
                onClick={() => setScope("task")}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  scope === "task"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/60"
                }`}
              >
                By Task
              </button>
              <button
                onClick={() => setScope("agent")}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  scope === "agent"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/60"
                }`}
              >
                By Agent
              </button>
            </div>

            <div className="text-xs text-slate-400 font-mono">
              {totalEvents} recorded event{totalEvents === 1 ? "" : "s"}
              {lastRefreshed && (
                <span className="text-slate-500 ml-2 hidden sm:inline">
                  (Synced at {lastRefreshed})
                </span>
              )}
            </div>
          </div>

          {/* Scope-Specific Selectors */}
          {scope === "project" && (
            <div className="flex flex-wrap items-center gap-3 pt-1">
              <span className="text-xs text-slate-400">Select Project:</span>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="bg-[#0c1017] border border-[#1e2738] text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500"
              >
                <option value="">-- Choose a project --</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {scope === "task" && (
            <div className="flex flex-wrap items-center gap-3 pt-1">
              <span className="text-xs text-slate-400">Task ID:</span>
              <input
                type="text"
                value={selectedTaskId}
                onChange={(e) => setSelectedTaskId(e.target.value)}
                placeholder="Paste UUID (e.g. tsk-xxxx)"
                className="bg-[#0c1017] border border-[#1e2738] text-xs text-slate-200 rounded-lg px-3 py-1.5 w-64 focus:outline-none focus:border-indigo-500"
              />
            </div>
          )}

          {scope === "agent" && (
            <div className="flex flex-wrap items-center gap-3 pt-1">
              <span className="text-xs text-slate-400">Select Agent:</span>
              <select
                value={selectedAgentId}
                onChange={(e) => setSelectedAgentId(e.target.value)}
                className="bg-[#0c1017] border border-[#1e2738] text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500"
              >
                <option value="">-- Choose an agent --</option>
                {agents.map((ag) => (
                  <option key={ag.id} value={ag.id}>
                    {ag.name} ({ag.role})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Search & Category Pills */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
            {/* Search Input */}
            <div className="relative flex-1 max-w-md">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search event narratives..."
                className="w-full pl-9 pr-8 py-1.5 bg-[#0c1017] border border-[#1e2738] rounded-lg text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 transition"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>

            {/* Category Filter Pills */}
            <div className="flex flex-wrap items-center gap-1.5">
              <button
                onClick={() => setCategoryFilter("ALL")}
                className={`px-2.5 py-1 rounded text-xs transition ${
                  categoryFilter === "ALL"
                    ? "bg-slate-700 text-white font-medium"
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                }`}
              >
                All
              </button>
              <button
                onClick={() => setCategoryFilter("PROJECT_CREATED")}
                className={`px-2.5 py-1 rounded text-xs transition ${
                  categoryFilter === "PROJECT_CREATED"
                    ? "bg-blue-500/20 text-blue-400 font-medium border border-blue-500/30"
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                }`}
              >
                Projects
              </button>
              <button
                onClick={() => setCategoryFilter("TASK_STATUS_CHANGED")}
                className={`px-2.5 py-1 rounded text-xs transition ${
                  categoryFilter === "TASK_STATUS_CHANGED"
                    ? "bg-amber-500/20 text-amber-400 font-medium border border-amber-500/30"
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                }`}
              >
                Tasks
              </button>
              <button
                onClick={() => setCategoryFilter("APPROVAL_RESOLVED")}
                className={`px-2.5 py-1 rounded text-xs transition ${
                  categoryFilter === "APPROVAL_RESOLVED"
                    ? "bg-rose-500/20 text-rose-400 font-medium border border-rose-500/30"
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                }`}
              >
                Approvals
              </button>
              <button
                onClick={() => setCategoryFilter("DECISION_RECORDED")}
                className={`px-2.5 py-1 rounded text-xs transition ${
                  categoryFilter === "DECISION_RECORDED"
                    ? "bg-purple-500/20 text-purple-400 font-medium border border-purple-500/30"
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                }`}
              >
                Decisions
              </button>
            </div>
          </div>
        </div>

        {/* Timeline Feed Container */}
        <div className="bg-[#111724] border border-[#1e2738] rounded-xl p-6">
          {loading && events.length === 0 ? (
            <div className="py-16 flex flex-col items-center justify-center text-center">
              <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mb-3" />
              <p className="text-xs text-slate-400">Loading company activity stream...</p>
            </div>
          ) : events.length === 0 ? (
            <div className="py-16 flex flex-col items-center justify-center text-center px-4">
              <div className="w-12 h-12 rounded-xl bg-slate-800/60 border border-slate-700/60 text-slate-400 flex items-center justify-center mb-4">
                <Activity className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-semibold text-white mb-1">
                No Activity Events Found
              </h3>
              <p className="text-xs text-slate-400 max-w-md leading-relaxed mb-4">
                No events match your current scope or filter criteria. Perform actions such as creating projects, updating tasks on the Kanban board, or recording company decisions to populate the feed.
              </p>
              <button
                onClick={() => {
                  setCategoryFilter("ALL");
                  setSearchQuery("");
                  setScope("company");
                }}
                className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white transition"
              >
                Reset Filters
              </button>
            </div>
          ) : (
            <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-3 before:bottom-3 before:w-0.5 before:bg-[#1e2738]">
              {events.map((event) => {
                const config = EVENT_TYPE_CATEGORIES[event.event_type] || {
                  label: event.event_type,
                  bg: "bg-slate-500/10",
                  text: "text-slate-400",
                  border: "border-slate-500/20",
                  icon: Activity,
                };
                const Icon = config.icon;

                return (
                  <div key={event.id} className="relative group">
                    {/* Timeline Node Icon */}
                    <div className="absolute -left-[30px] top-1.5 w-6 h-6 rounded-full bg-[#0c1017] border-2 border-[#1e2738] group-hover:border-indigo-500 text-slate-400 group-hover:text-indigo-400 flex items-center justify-center transition shadow-sm">
                      <Icon className="w-3 h-3" />
                    </div>

                    {/* Event Card */}
                    <div className="bg-[#0c1017] border border-[#1e2738] hover:border-slate-700/80 rounded-xl p-4 transition-all space-y-2.5">
                      {/* Top Bar: Category, Actor, Timestamp */}
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded ${config.bg} ${config.text} border ${config.border}`}
                          >
                            {config.label}
                          </span>

                          {/* Actor Badge */}
                          <div className="inline-flex items-center gap-1.5 text-xs text-slate-300">
                            {event.actor_type === "agent" ? (
                              <span className="inline-flex items-center gap-1 text-[11px] text-purple-400">
                                <Bot className="w-3 h-3" />
                                <span>Agent</span>
                              </span>
                            ) : event.actor_type === "user" ? (
                              <span className="inline-flex items-center gap-1 text-[11px] text-indigo-400">
                                <UserIcon className="w-3 h-3" />
                                <span>Operator</span>
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-[11px] text-slate-400">
                                <Building2 className="w-3 h-3" />
                                <span>System</span>
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Relative Timestamp */}
                        <div
                          className="flex items-center gap-1.5 text-xs text-slate-400 font-mono"
                          title={new Date(event.created_at).toLocaleString()}
                        >
                          <Clock className="w-3 h-3 text-slate-500" />
                          <span>{formatRelativeTime(event.created_at)}</span>
                        </div>
                      </div>

                      {/* Event Narrative Message */}
                      <div className="text-sm font-medium text-white leading-relaxed">
                        {event.message}
                      </div>

                      {/* Association Chips & Details Button */}
                      <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-[#1e2738]/50 text-xs">
                        <div className="flex flex-wrap items-center gap-2">
                          {event.project_id && (
                            <Link
                              href={`/projects/${event.project_id}/board`}
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 text-[11px] font-mono transition"
                            >
                              <FolderGit2 className="w-3 h-3" />
                              <span>Project Board</span>
                            </Link>
                          )}
                          {event.task_id && (
                            <Link
                              href="/tasks"
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20 text-[11px] font-mono transition"
                            >
                              <CheckSquare className="w-3 h-3" />
                              <span>Task Console</span>
                            </Link>
                          )}
                        </div>

                        {/* Metadata button */}
                        {event.metadata && Object.keys(event.metadata).length > 0 && (
                          <button
                            onClick={() => setInspectEvent(event)}
                            className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 transition"
                          >
                            <Eye className="w-3 h-3" />
                            <span>Inspect Context</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Metadata Inspection Modal */}
        {inspectEvent && (
          <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#111724] border border-[#1e2738] rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-[#1e2738]">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-indigo-400" />
                  <h3 className="text-sm font-semibold text-white">Event Context Data</h3>
                </div>
                <button
                  onClick={() => setInspectEvent(null)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2">
                <div className="text-xs text-slate-400 font-mono">
                  Event ID: <span className="text-slate-200">{inspectEvent.id}</span>
                </div>
                <div className="text-xs text-slate-400 font-mono">
                  Event Type: <span className="text-indigo-400">{inspectEvent.event_type}</span>
                </div>
                <div className="text-xs text-slate-400 font-mono">
                  Timestamp:{" "}
                  <span className="text-slate-300">
                    {new Date(inspectEvent.created_at).toLocaleString()}
                  </span>
                </div>
              </div>

              <div>
                <span className="text-xs text-slate-400 block mb-1 font-medium">
                  Structured Payload:
                </span>
                <pre className="p-3 bg-[#0c1017] border border-[#1e2738] rounded-lg text-xs font-mono text-slate-300 overflow-x-auto max-h-60">
                  {JSON.stringify(inspectEvent.metadata, null, 2)}
                </pre>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  onClick={() => setInspectEvent(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-white rounded-lg transition"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </ShellLayout>
  );
}
