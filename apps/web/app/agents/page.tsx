"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Bot,
  Building2,
  Check,
  ChevronRight,
  Clock,
  Cpu,
  FolderGit2,
  GitFork,
  History,
  Plus,
  Radio,
  RefreshCw,
  Search,
  Shield,
  Sliders,
  Sparkles,
  Users,
  X,
} from "lucide-react";
import {
  Agent,
  AgentDetail,
  AgentPresence,
  Company,
  Department,
  PresenceStatus,
  PresenceSummary,
  api,
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

export default function AgentsPage() {
  const [loading, setLoading] = useState(true);
  const [activeCompany, setActiveCompany] = useState<Company | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [agentDetail, setAgentDetail] = useState<AgentDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [provisioning, setProvisioning] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDeptFilter, setSelectedDeptFilter] = useState("all");
  const [selectedTypeFilter, setSelectedTypeFilter] = useState("all");
  const [selectedPresenceFilter, setSelectedPresenceFilter] = useState("all");

  // Presence State (Phase 14)
  const [presenceMap, setPresenceMap] = useState<Record<string, AgentPresence>>({});
  const [presenceSummary, setPresenceSummary] = useState<PresenceSummary | null>(null);
  const [updatingPresenceId, setUpdatingPresenceId] = useState<string | null>(null);

  // Registration Modal
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [creatingAgent, setCreatingAgent] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: "",
    role: "",
    type: "specialist",
    department_id: "",
    reports_to: "",
    mission: "",
    authority_level: "specialist",
    system_prompt: "",
    model: "gemini-1.5-pro",
    capabilities: "domain_planning, structured_reasoning",
    tools: "web_search, document_reader",
  });

  // New Version Modal inside Drawer
  const [showVersionModal, setShowVersionModal] = useState(false);
  const [creatingVersion, setCreatingVersion] = useState(false);
  const [versionForm, setVersionForm] = useState({
    version: "",
    system_prompt: "",
    model: "gemini-1.5-pro",
    capabilities: "",
    tools: "",
  });

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const companies = await api.getCompanies();
      if (companies.length > 0) {
        const primaryCompany = companies[0];
        setActiveCompany(primaryCompany);
        const [agentsList, deptsList, presenceRes, summaryRes] = await Promise.all([
          api.getAgents(primaryCompany.id),
          api.getDepartments(primaryCompany.id),
          api.getCompanyPresence(primaryCompany.id).catch(() => ({ items: [], total: 0 })),
          api.getPresenceSummary(primaryCompany.id).catch(() => null),
        ]);
        setAgents(agentsList);
        setDepartments(deptsList);
        const map: Record<string, AgentPresence> = {};
        for (const p of presenceRes.items) {
          map[p.agent_id] = p;
        }
        setPresenceMap(map);
        setPresenceSummary(summaryRes);
      } else {
        setActiveCompany(null);
        setAgents([]);
        setDepartments([]);
        setPresenceMap({});
        setPresenceSummary(null);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load agent registry.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function openAgentDetail(agentId: string) {
    if (!activeCompany) return;
    setSelectedAgentId(agentId);
    setDetailLoading(true);
    try {
      const detail = await api.getAgent(activeCompany.id, agentId);
      setAgentDetail(detail);
      setVersionForm({
        version: `${(parseFloat(detail.current_definition?.version || "1.0") + 0.1).toFixed(1)}`,
        system_prompt: detail.current_definition?.system_prompt || "",
        model: detail.current_definition?.model || "gemini-1.5-pro",
        capabilities: (detail.current_definition?.capabilities || []).join(", "),
        tools: (detail.current_definition?.tools || []).join(", "),
      });
    } catch {
      // Handled gracefully
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleProvisionDefaults() {
    if (!activeCompany) return;
    setProvisioning(true);
    setError(null);
    try {
      const provisioned = await api.provisionDefaultAgents(activeCompany.id);
      setAgents(provisioned);
      setActionSuccess("Foundational 11 agents successfully registered!");
      setTimeout(() => setActionSuccess(null), 4000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to provision default organization.");
    } finally {
      setProvisioning(false);
    }
  }

  async function handleRegisterAgent(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompany) return;
    setCreatingAgent(true);
    setError(null);
    try {
      const caps = createForm.capabilities
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      const tools = createForm.tools
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);

      const created = await api.createAgent(activeCompany.id, {
        name: createForm.name,
        role: createForm.role,
        type: createForm.type,
        department_id: createForm.department_id || null,
        reports_to: createForm.reports_to || null,
        mission: createForm.mission || undefined,
        authority_level: createForm.authority_level,
        system_prompt: createForm.system_prompt || undefined,
        model: createForm.model,
        capabilities: caps,
        tools: tools,
      });

      setAgents((prev) => [...prev, created]);
      setShowRegisterModal(false);
      setCreateForm({
        name: "",
        role: "",
        type: "specialist",
        department_id: "",
        reports_to: "",
        mission: "",
        authority_level: "specialist",
        system_prompt: "",
        model: "gemini-1.5-pro",
        capabilities: "domain_planning, structured_reasoning",
        tools: "web_search, document_reader",
      });
      setActionSuccess(`Agent ${created.name} successfully registered.`);
      setTimeout(() => setActionSuccess(null), 4000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to register agent.");
    } finally {
      setCreatingAgent(false);
    }
  }

  async function handleCreateVersion(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompany || !selectedAgentId) return;
    setCreatingVersion(true);
    setError(null);
    try {
      const caps = versionForm.capabilities
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      const tools = versionForm.tools
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);

      const newDef = await api.createAgentDefinition(
        activeCompany.id,
        selectedAgentId,
        {
          version: versionForm.version,
          system_prompt: versionForm.system_prompt || undefined,
          model: versionForm.model,
          capabilities: caps,
          tools: tools,
        }
      );

      // Refresh detail
      const updated = await api.getAgent(activeCompany.id, selectedAgentId);
      setAgentDetail(updated);
      setAgents((prev) =>
        prev.map((a) => (a.id === selectedAgentId ? updated : a))
      );
      setShowVersionModal(false);
      setActionSuccess(`Definition version ${newDef.version} created.`);
      setTimeout(() => setActionSuccess(null), 4000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create definition version.");
    } finally {
      setCreatingVersion(false);
    }
  }

  async function handleToggleStatus(agent: Agent) {
    if (!activeCompany) return;
    const nextStatus = agent.status === "active" ? "inactive" : "active";
    try {
      const updated = await api.updateAgent(activeCompany.id, agent.id, {
        status: nextStatus,
      });
      setAgents((prev) => prev.map((a) => (a.id === agent.id ? updated : a)));
      if (agentDetail && agentDetail.id === agent.id) {
        setAgentDetail((prev) => (prev ? { ...prev, status: nextStatus } : null));
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to toggle agent status.");
    }
  }

  async function handleUpdatePresenceStatus(agentId: string, status: PresenceStatus) {
    if (!activeCompany) return;
    setUpdatingPresenceId(agentId);
    try {
      const updated = await api.updateAgentPresence(activeCompany.id, agentId, { status });
      setPresenceMap((prev) => ({ ...prev, [agentId]: updated }));
      const sum = await api.getPresenceSummary(activeCompany.id).catch(() => null);
      if (sum) setPresenceSummary(sum);
      setActionSuccess(`Agent operational presence updated to ${status}.`);
      setTimeout(() => setActionSuccess(null), 4000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update agent presence.");
    } finally {
      setUpdatingPresenceId(null);
    }
  }

  const filteredAgents = agents.filter((a) => {
    const matchesQuery =
      searchQuery === "" ||
      a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.role.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (a.mission && a.mission.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesDept =
      selectedDeptFilter === "all" || a.department_id === selectedDeptFilter;

    const matchesType =
      selectedTypeFilter === "all" || a.type === selectedTypeFilter;

    const p = presenceMap[a.id];
    const presenceStatus = p?.status || (a.status === "active" ? "IDLE" : "OFFLINE");
    const matchesPresence =
      selectedPresenceFilter === "all" ||
      (selectedPresenceFilter === "WORKING" && presenceStatus === "WORKING") ||
      (selectedPresenceFilter === "IDLE" && presenceStatus === "IDLE") ||
      (selectedPresenceFilter === "WAITING" && presenceStatus === "WAITING") ||
      (selectedPresenceFilter === "ATTENTION" && (presenceStatus === "BLOCKED" || presenceStatus === "ERROR")) ||
      (selectedPresenceFilter === "OFFLINE" && presenceStatus === "OFFLINE");

    return matchesQuery && matchesDept && matchesType && matchesPresence;
  });

  const activeCount = agents.filter((a) => a.status === "active").length;
  const inactiveCount = agents.filter((a) => a.status !== "active").length;

  return (
    <ShellLayout pageTitle="Agent Registry" breadcrumb="Organization">
      <div className="space-y-8">
        {/* Executive Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-[#1e2738]">
          <div>
            <div className="flex flex-wrap items-center gap-3 mb-1">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                Agent Registry
              </h1>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                Phase 14 Active: Agent Presence
              </span>
              {activeCompany && (
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  {activeCompany.name}
                </span>
              )}
            </div>
            <p className="text-xs sm:text-sm text-slate-400">
              Authoritative catalog of organizational AI agents, reporting relationships, and real-time operational presence telemetry.
            </p>
          </div>

          {activeCompany && (
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={loadData}
                disabled={loading}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[#1e2738] bg-[#111724] hover:bg-[#182030] text-xs font-medium text-slate-300 hover:text-white transition disabled:opacity-50"
                aria-label="Refresh agent registry"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-indigo-400" : ""}`} />
                <span>Refresh</span>
              </button>

              {agents.length === 0 && (
                <button
                  onClick={handleProvisionDefaults}
                  disabled={provisioning}
                  className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition disabled:opacity-50"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{provisioning ? "Provisioning..." : "Provision Default Organization"}</span>
                </button>
              )}

              <button
                onClick={() => setShowRegisterModal(true)}
                className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-[#182030] hover:bg-[#202b40] border border-indigo-500/40 text-xs font-semibold text-indigo-300 hover:text-white transition"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Register Agent</span>
              </button>
            </div>
          )}
        </div>

        {/* Alerts */}
        {error && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-rose-400 hover:text-rose-200">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {actionSuccess && (
          <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{actionSuccess}</span>
          </div>
        )}

        {/* State 1: No Company Provisioned */}
        {!loading && !activeCompany && (
          <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/5 p-8 text-center max-w-xl mx-auto space-y-4">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center mx-auto">
              <Building2 className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-white">No Company Provisioned</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Agent Registry requires an authoritative company entity. Provision your company and departments in Company Management to register AI agents.
            </p>
            <Link
              href="/company"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition"
            >
              <span>Setup Company</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        )}

        {/* State 2: Company Exists */}
        {activeCompany && (
          <>
            {/* Registry & Operational Presence Overview */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl border border-[#1e2738] bg-[#111724]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-slate-400 font-medium uppercase">Registered Agents</span>
                  <Users className="w-4 h-4 text-indigo-400" />
                </div>
                <div className="text-2xl font-bold font-mono text-white">{agents.length}</div>
                <p className="text-[11px] text-slate-400 pt-1 font-mono">Total definitions in PostgreSQL</p>
              </div>

              <div className="p-4 rounded-xl border border-[#1e2738] bg-[#111724]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-slate-400 font-medium uppercase">Working Now</span>
                  <Radio
                    className={`w-4 h-4 ${
                      presenceSummary && presenceSummary.working_count > 0
                        ? "text-emerald-400 animate-pulse"
                        : "text-slate-500"
                    }`}
                  />
                </div>
                <div
                  className={`text-2xl font-bold font-mono ${
                    presenceSummary && presenceSummary.working_count > 0
                      ? "text-emerald-400"
                      : "text-white"
                  }`}
                >
                  {presenceSummary ? presenceSummary.working_count : 0}
                </div>
                <p className="text-[11px] text-slate-400 pt-1 font-mono">Active task executions</p>
              </div>

              <div className="p-4 rounded-xl border border-[#1e2738] bg-[#111724]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-slate-400 font-medium uppercase">Idle / Standby</span>
                  <Check className="w-4 h-4 text-blue-400" />
                </div>
                <div className="text-2xl font-bold font-mono text-blue-400">
                  {presenceSummary ? presenceSummary.idle_count : activeCount}
                </div>
                <p className="text-[11px] text-slate-400 pt-1 font-mono">Ready for assignment</p>
              </div>

              <div className="p-4 rounded-xl border border-[#1e2738] bg-[#111724]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-slate-400 font-medium uppercase">Attention / Waiting</span>
                  <AlertTriangle
                    className={`w-4 h-4 ${
                      (presenceSummary?.waiting_count || 0) +
                        (presenceSummary?.blocked_count || 0) +
                        (presenceSummary?.error_count || 0) >
                      0
                        ? "text-amber-400"
                        : "text-slate-500"
                    }`}
                  />
                </div>
                <div
                  className={`text-2xl font-bold font-mono ${
                    (presenceSummary?.waiting_count || 0) +
                      (presenceSummary?.blocked_count || 0) +
                      (presenceSummary?.error_count || 0) >
                    0
                      ? "text-amber-400"
                      : "text-slate-400"
                  }`}
                >
                  {presenceSummary
                    ? presenceSummary.waiting_count +
                      presenceSummary.blocked_count +
                      presenceSummary.error_count
                    : 0}
                </div>
                <p className="text-[11px] text-slate-400 pt-1 font-mono">
                  {presenceSummary
                    ? `${presenceSummary.waiting_count} wait · ${presenceSummary.blocked_count} block · ${presenceSummary.error_count} err`
                    : "No attention required"}
                </p>
              </div>
            </div>

            {/* Filter & Search Bar */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3 rounded-xl border border-[#1e2738] bg-[#111724]">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter agents by name, role, or mission..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
                />
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <select
                  value={selectedDeptFilter}
                  onChange={(e) => setSelectedDeptFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs text-slate-300 focus:outline-none focus:border-indigo-500 transition"
                  aria-label="Filter by department"
                >
                  <option value="all">All Departments</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.code.toUpperCase()})
                    </option>
                  ))}
                </select>

                <select
                  value={selectedTypeFilter}
                  onChange={(e) => setSelectedTypeFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs text-slate-300 focus:outline-none focus:border-indigo-500 transition"
                  aria-label="Filter by agent type"
                >
                  <option value="all">All Types</option>
                  <option value="executive">Executive</option>
                  <option value="department_head">Department Head</option>
                  <option value="specialist">Specialist</option>
                </select>

                <select
                  value={selectedPresenceFilter}
                  onChange={(e) => setSelectedPresenceFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs text-slate-300 focus:outline-none focus:border-indigo-500 transition font-mono"
                  aria-label="Filter by presence status"
                >
                  <option value="all">All Presences</option>
                  <option value="WORKING">● Working</option>
                  <option value="IDLE">○ Idle</option>
                  <option value="WAITING">◐ Waiting</option>
                  <option value="ATTENTION">! Attention Required</option>
                  <option value="OFFLINE">— Offline</option>
                </select>
              </div>
            </div>


            {/* Agent Grid or Empty State */}
            {filteredAgents.length === 0 ? (
              <div className="rounded-xl border border-dashed border-[#1e2738] bg-[#111724]/40 p-12 text-center">
                <div className="w-12 h-12 rounded-xl bg-slate-800 text-slate-400 flex items-center justify-center mx-auto mb-3">
                  <Bot className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-semibold text-white mb-1">No Agents Found</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4">
                  {agents.length === 0
                    ? "No AI agents have been registered for this company yet. You can provision the 11 foundational initial agents with one click."
                    : "No registered agents match the selected search or filter criteria."}
                </p>
                {agents.length === 0 && (
                  <button
                    onClick={handleProvisionDefaults}
                    disabled={provisioning}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition disabled:opacity-50"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>{provisioning ? "Provisioning..." : "Provision Default Organization"}</span>
                  </button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredAgents.map((agent) => {
                  const presence = presenceMap[agent.id];
                  const pStatus = presence?.status || (agent.status === "active" ? "IDLE" : "OFFLINE");
                  const isWorking = pStatus === "WORKING";
                  const isIdle = pStatus === "IDLE";
                  const isWaiting = pStatus === "WAITING";
                  const isBlocked = pStatus === "BLOCKED";
                  const isError = pStatus === "ERROR";

                  const badgeClass = isWorking
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : isWaiting
                    ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                    : isBlocked
                    ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                    : isError
                    ? "bg-red-500/10 text-red-400 border-red-500/30"
                    : isIdle
                    ? "bg-blue-500/10 text-blue-400 border-blue-500/30"
                    : "bg-slate-800 text-slate-400 border-slate-700";

                  return (
                    <div
                      key={agent.id}
                      className={`rounded-xl border p-5 flex flex-col justify-between transition-all space-y-4 ${
                        isWorking
                          ? "bg-[#0d141e] border-emerald-500/30 shadow-sm shadow-emerald-500/5 hover:border-emerald-500/50"
                          : "bg-[#111724] border-[#1e2738] hover:border-slate-700"
                      }`}
                    >
                      <div>
                        {/* Header: Name, Role & Operational Presence Badge */}
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <div className="min-w-0">
                            <div className="flex items-center gap-2 flex-wrap mb-0.5">
                              <h3 className="text-sm font-semibold text-white truncate">{agent.name}</h3>
                              <span
                                className={`text-[10px] font-mono px-2 py-0.5 rounded uppercase font-semibold ${
                                  agent.type === "executive"
                                    ? "bg-purple-500/10 text-purple-400 border border-purple-500/30"
                                    : agent.type === "department_head"
                                    ? "bg-blue-500/10 text-blue-400 border border-blue-500/30"
                                    : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                }`}
                              >
                                {agent.type.replace("_", " ")}
                              </span>
                            </div>
                            <p className="text-xs text-slate-400 font-medium truncate">{agent.role}</p>
                          </div>

                          {/* Presence Status Badge */}
                          <div className="flex flex-col items-end gap-1 shrink-0">
                            <span
                              className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-medium border ${badgeClass}`}
                            >
                              {isWorking ? (
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                              ) : isWaiting ? (
                                <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                              ) : isBlocked || isError ? (
                                <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
                              ) : isIdle ? (
                                <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                              ) : (
                                <span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>
                              )}
                              <span>{pStatus}</span>
                            </span>
                          </div>
                        </div>

                        {agent.mission && (
                          <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed mb-3">
                            {agent.mission}
                          </p>
                        )}

                        {/* Operational Activity & Execution Telemetry per docs/UI.md § 76 */}
                        <div className="p-2.5 mb-3 rounded-lg bg-[#0a0e14] border border-[#1e2738] space-y-1.5 text-xs font-mono text-[11px]">
                          <div className="flex items-center justify-between">
                            <span className="text-slate-500 flex items-center gap-1">
                              <Activity className="w-3 h-3 text-slate-400" />
                              <span>Activity</span>
                            </span>
                            <span
                              className="text-slate-200 truncate max-w-[170px]"
                              title={presence?.current_activity || (isIdle ? "Idle · Awaiting Task" : "Standby")}
                            >
                              {presence?.current_activity || (isIdle ? "Idle · Awaiting Task" : "Standby")}
                            </span>
                          </div>

                          {presence?.current_task_title && (
                            <div className="flex items-center justify-between">
                              <span className="text-slate-500">Task</span>
                              <Link
                                href="/tasks"
                                className="text-indigo-400 hover:text-indigo-300 truncate max-w-[170px]"
                                title={presence.current_task_title}
                              >
                                {presence.current_task_title}
                              </Link>
                            </div>
                          )}

                          {isWorking && presence.duration_seconds > 0 && (
                            <div className="flex items-center justify-between">
                              <span className="text-slate-500 flex items-center gap-1">
                                <Clock className="w-3 h-3 text-slate-400" />
                                <span>Duration</span>
                              </span>
                              <span className="text-emerald-400 font-semibold">
                                {formatDuration(presence.duration_seconds)}
                              </span>
                            </div>
                          )}

                          <div className="flex items-center justify-between text-[10px] pt-1 border-t border-[#1e2738]/60">
                            <span className="text-slate-500">Heartbeat</span>
                            <span className={presence?.is_stale ? "text-amber-400" : "text-slate-400"}>
                              {presence?.last_heartbeat_at
                                ? formatRelativeTime(presence.last_heartbeat_at)
                                : "Never"}
                              {presence?.is_stale && " (Stale)"}
                            </span>
                          </div>
                        </div>

                        {/* Structural Details */}
                        <div className="space-y-1.5 text-xs text-slate-400 pt-2 border-t border-[#1e2738]/80 font-mono text-[11px]">
                          <div className="flex items-center justify-between">
                            <span className="text-slate-500 flex items-center gap-1.5">
                              <Building2 className="w-3.5 h-3.5 text-slate-400" />
                              <span>Department</span>
                            </span>
                            <span className="text-slate-300">
                              {agent.department ? `${agent.department.code.toUpperCase()}` : "Executive Level"}
                            </span>
                          </div>

                          <div className="flex items-center justify-between">
                            <span className="text-slate-500 flex items-center gap-1.5">
                              <GitFork className="w-3.5 h-3.5 text-slate-400" />
                              <span>Reports To</span>
                            </span>
                            <span className="text-slate-300">
                              {agent.manager ? agent.manager.name : "None (Top Level)"}
                            </span>
                          </div>

                          <div className="flex items-center justify-between">
                            <span className="text-slate-500 flex items-center gap-1.5">
                              <Cpu className="w-3.5 h-3.5 text-slate-400" />
                              <span>Model & Version</span>
                            </span>
                            <span className="text-slate-300">
                              {agent.current_definition
                                ? `v${agent.current_definition.version} (${agent.current_definition.model})`
                                : "Unversioned"}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="pt-3 border-t border-[#1e2738] flex items-center justify-between">
                        <button
                          onClick={() => handleToggleStatus(agent)}
                          className={`text-[11px] font-mono px-2 py-0.5 rounded border transition ${
                            agent.status === "active"
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20"
                              : "bg-amber-500/10 text-amber-400 border-amber-500/30 hover:bg-amber-500/20"
                          }`}
                          title="Click to toggle registry active/inactive status"
                        >
                          Registry: {agent.status}
                        </button>
                        <button
                          onClick={() => openAgentDetail(agent.id)}
                          className="inline-flex items-center gap-1 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition"
                        >
                          <span>Inspect Definition</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}

        {/* Agent Detail Drawer */}
        {selectedAgentId && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex justify-end">
            <div className="w-full max-w-xl bg-[#0e1420] border-l border-[#1e2738] h-full overflow-y-auto p-6 flex flex-col justify-between">
              {detailLoading || !agentDetail ? (
                <div className="flex-1 flex items-center justify-center">
                  <RefreshCw className="w-6 h-6 animate-spin text-indigo-400" />
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Drawer Header */}
                  <div className="flex items-start justify-between pb-4 border-b border-[#1e2738]">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h2 className="text-lg font-bold text-white">{agentDetail.name}</h2>
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 uppercase">
                          {agentDetail.type.replace("_", " ")}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400">{agentDetail.role}</p>
                    </div>
                    <button
                      onClick={() => {
                        setSelectedAgentId(null);
                        setAgentDetail(null);
                      }}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Mission & Purpose */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Organizational Mission
                    </h4>
                    <div className="p-3.5 rounded-xl bg-[#111724] border border-[#1e2738] text-xs text-slate-300 leading-relaxed">
                      {agentDetail.mission || "No formal mission statement defined."}
                    </div>
                  </div>

                  {/* Hierarchy Placement */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Reporting Hierarchy
                    </h4>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 rounded-xl bg-[#111724] border border-[#1e2738]">
                        <span className="text-[11px] text-slate-500 block mb-1">Direct Manager</span>
                        <span className="text-xs font-medium text-white">
                          {agentDetail.manager ? `${agentDetail.manager.name} (${agentDetail.manager.role})` : "None (Top Level)"}
                        </span>
                      </div>
                      <div className="p-3 rounded-xl bg-[#111724] border border-[#1e2738]">
                        <span className="text-[11px] text-slate-500 block mb-1">Direct Subordinates</span>
                        <span className="text-xs font-medium text-white">
                          {agentDetail.subordinates.length} Direct Report{agentDetail.subordinates.length === 1 ? "" : "s"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Declared Capabilities & Tools */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Declared Capabilities & Tool Gateway References
                    </h4>
                    <div className="p-3.5 rounded-xl bg-[#111724] border border-[#1e2738] space-y-3">
                      <div>
                        <span className="text-[11px] text-slate-500 block mb-1.5">Capabilities:</span>
                        <div className="flex flex-wrap gap-1.5">
                          {(agentDetail.current_definition?.capabilities || []).map((cap) => (
                            <span
                              key={cap}
                              className="text-[11px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20"
                            >
                              {cap}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div>
                        <span className="text-[11px] text-slate-500 block mb-1.5">Tools Allowed by Policy:</span>
                        <div className="flex flex-wrap gap-1.5">
                          {(agentDetail.current_definition?.tools || []).map((t) => (
                            <span
                              key={t}
                              className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700"
                            >
                              {t}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* System Prompt Declaration */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                        Current System Prompt (v{agentDetail.current_definition?.version || "1.0"})
                      </h4>
                      <button
                        onClick={() => setShowVersionModal(!showVersionModal)}
                        className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                      >
                        {showVersionModal ? "Cancel" : "+ New Version"}
                      </button>
                    </div>

                    {showVersionModal ? (
                      <form onSubmit={handleCreateVersion} className="p-4 rounded-xl bg-[#111724] border border-indigo-500/30 space-y-3">
                        <div>
                          <label className="block text-[11px] text-slate-400 mb-1">Version Identifier</label>
                          <input
                            type="text"
                            value={versionForm.version}
                            onChange={(e) => setVersionForm({ ...versionForm, version: e.target.value })}
                            className="w-full px-3 py-1.5 rounded bg-[#0c1017] border border-[#1e2738] text-xs text-white"
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] text-slate-400 mb-1">System Prompt</label>
                          <textarea
                            rows={3}
                            value={versionForm.system_prompt}
                            onChange={(e) => setVersionForm({ ...versionForm, system_prompt: e.target.value })}
                            className="w-full px-3 py-1.5 rounded bg-[#0c1017] border border-[#1e2738] text-xs text-white font-mono"
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] text-slate-400 mb-1">Capabilities (comma-separated)</label>
                          <input
                            type="text"
                            value={versionForm.capabilities}
                            onChange={(e) => setVersionForm({ ...versionForm, capabilities: e.target.value })}
                            className="w-full px-3 py-1.5 rounded bg-[#0c1017] border border-[#1e2738] text-xs text-white"
                          />
                        </div>
                        <button
                          type="submit"
                          disabled={creatingVersion}
                          className="w-full py-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition disabled:opacity-50"
                        >
                          {creatingVersion ? "Saving Version..." : "Save Definition Version"}
                        </button>
                      </form>
                    ) : (
                      <pre className="p-3.5 rounded-xl bg-[#111724] border border-[#1e2738] text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">
                        {agentDetail.current_definition?.system_prompt || "No system prompt configured."}
                      </pre>
                    )}
                  </div>

                  {/* Version History */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <History className="w-3.5 h-3.5 text-slate-400" />
                      <span>Definition Version History ({agentDetail.definitions.length})</span>
                    </h4>
                    <div className="space-y-2">
                      {agentDetail.definitions.map((def) => (
                        <div
                          key={def.id}
                          className="p-3 rounded-lg bg-[#111724] border border-[#1e2738] flex items-center justify-between text-xs font-mono"
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-white">v{def.version}</span>
                            <span className="text-slate-400 font-sans text-[11px]">({def.model})</span>
                            {def.is_current && (
                              <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                                Current
                              </span>
                            )}
                          </div>
                          <span className="text-[11px] text-slate-500">
                            {new Date(def.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Real-time Agent Presence & Telemetry (Phase 14) */}
                  <div className="space-y-3 pt-2 border-t border-[#1e2738]">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                        <Radio className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Real-Time Presence & Telemetry</span>
                      </h4>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        Phase 14
                      </span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-[#111724] border border-[#1e2738] space-y-2.5 font-mono text-[11px]">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">Presence Status:</span>
                        <div className="flex items-center gap-2">
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono border ${
                              presenceMap[agentDetail.id]?.status === "WORKING"
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                                : presenceMap[agentDetail.id]?.status === "WAITING"
                                ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                                : presenceMap[agentDetail.id]?.status === "BLOCKED"
                                ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                                : presenceMap[agentDetail.id]?.status === "ERROR"
                                ? "bg-red-500/10 text-red-400 border-red-500/30"
                                : "bg-blue-500/10 text-blue-400 border-blue-500/30"
                            }`}
                          >
                            {presenceMap[agentDetail.id]?.status === "WORKING" && (
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                            )}
                            <span>{presenceMap[agentDetail.id]?.status || "IDLE"}</span>
                          </span>

                          <select
                            value={presenceMap[agentDetail.id]?.status || "IDLE"}
                            disabled={updatingPresenceId === agentDetail.id}
                            onChange={(e) =>
                              handleUpdatePresenceStatus(agentDetail.id, e.target.value as PresenceStatus)
                            }
                            className="px-2 py-0.5 rounded bg-[#0c1017] border border-[#1e2738] text-[10px] text-slate-300 font-sans cursor-pointer focus:outline-none focus:border-indigo-500"
                            title="Override agent presence status"
                          >
                            <option value="ONLINE">ONLINE</option>
                            <option value="IDLE">IDLE</option>
                            <option value="WORKING">WORKING</option>
                            <option value="WAITING">WAITING</option>
                            <option value="BLOCKED">BLOCKED</option>
                            <option value="ERROR">ERROR</option>
                            <option value="OFFLINE">OFFLINE</option>
                          </select>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">Current Activity:</span>
                        <span className="text-slate-300 truncate max-w-[240px]">
                          {presenceMap[agentDetail.id]?.current_activity || "Idle / Awaiting Task"}
                        </span>
                      </div>

                      {presenceMap[agentDetail.id]?.current_task_title && (
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">Active Task:</span>
                          <span className="text-indigo-400 truncate max-w-[240px]">
                            {presenceMap[agentDetail.id]?.current_task_title}
                          </span>
                        </div>
                      )}

                      {presenceMap[agentDetail.id]?.current_project_name && (
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">Active Project:</span>
                          <span className="text-slate-300 truncate max-w-[240px]">
                            {presenceMap[agentDetail.id]?.current_project_name}
                          </span>
                        </div>
                      )}

                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">Active Duration:</span>
                        <span className="text-emerald-400 font-mono">
                          {formatDuration(presenceMap[agentDetail.id]?.duration_seconds || 0)}
                        </span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">Heartbeat:</span>
                        <span className={presenceMap[agentDetail.id]?.is_stale ? "text-amber-400" : "text-slate-400"}>
                          {presenceMap[agentDetail.id]?.last_heartbeat_at
                            ? formatRelativeTime(presenceMap[agentDetail.id].last_heartbeat_at)
                            : "Never"}
                          {presenceMap[agentDetail.id]?.is_stale && " · Stale (>60s)"}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Register Agent Modal */}
        {showRegisterModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="w-full max-w-xl rounded-2xl bg-[#0e1420] border border-[#1e2738] p-6 space-y-6 shadow-2xl max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between pb-3 border-b border-[#1e2738]">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    <Bot className="w-4 h-4" />
                  </div>
                  <h3 className="text-sm font-semibold text-white">Register New Agent</h3>
                </div>
                <button
                  onClick={() => setShowRegisterModal(false)}
                  className="text-slate-400 hover:text-white transition"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleRegisterAgent} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Agent Display Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Lead Security Architect"
                      value={createForm.name}
                      onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Role / Title</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Security Specialist"
                      value={createForm.role}
                      onChange={(e) => setCreateForm({ ...createForm, role: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Type</label>
                    <select
                      value={createForm.type}
                      onChange={(e) => setCreateForm({ ...createForm, type: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs text-slate-300 focus:outline-none focus:border-indigo-500 transition"
                    >
                      <option value="specialist">Specialist</option>
                      <option value="department_head">Department Head</option>
                      <option value="executive">Executive</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Department</label>
                    <select
                      value={createForm.department_id}
                      onChange={(e) => setCreateForm({ ...createForm, department_id: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs text-slate-300 focus:outline-none focus:border-indigo-500 transition"
                    >
                      <option value="">Executive Level (None)</option>
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name} ({d.code.toUpperCase()})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Reports To (Manager)</label>
                    <select
                      value={createForm.reports_to}
                      onChange={(e) => setCreateForm({ ...createForm, reports_to: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs text-slate-300 focus:outline-none focus:border-indigo-500 transition"
                    >
                      <option value="">None (Top Level)</option>
                      {agents.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.name} ({a.role})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Mission / Objective</label>
                  <textarea
                    rows={2}
                    placeholder="State the core objective, focus areas, and mandate for this agent..."
                    value={createForm.mission}
                    onChange={(e) => setCreateForm({ ...createForm, mission: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Initial System Prompt</label>
                  <textarea
                    rows={3}
                    placeholder="Define the primary behavioral directives and reasoning style..."
                    value={createForm.system_prompt}
                    onChange={(e) => setCreateForm({ ...createForm, system_prompt: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs text-white placeholder-slate-500 font-mono focus:outline-none focus:border-indigo-500 transition"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Capabilities (comma-separated)</label>
                    <input
                      type="text"
                      value={createForm.capabilities}
                      onChange={(e) => setCreateForm({ ...createForm, capabilities: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Tools (comma-separated)</label>
                    <input
                      type="text"
                      value={createForm.tools}
                      onChange={(e) => setCreateForm({ ...createForm, tools: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
                    />
                  </div>
                </div>

                <div className="pt-4 border-t border-[#1e2738] flex items-center justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setShowRegisterModal(false)}
                    className="px-4 py-2 rounded-lg border border-[#1e2738] text-xs font-medium text-slate-300 hover:text-white transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={creatingAgent}
                    className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition disabled:opacity-50"
                  >
                    {creatingAgent ? "Registering..." : "Register Agent"}
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
