"use client";

import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Building2,
  CheckCircle2,
  Clock,
  Code2,
  ExternalLink,
  Eye,
  FileText,
  Filter,
  Github,
  Globe,
  Play,
  RefreshCw,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Terminal,
  User as UserIcon,
  Wrench,
  X,
} from "lucide-react";
import {
  Agent,
  api,
  Company,
  ToolDefinition,
  ToolExecutionRecord,
} from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

export default function ToolGatewayPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [activeCompany, setActiveCompany] = useState<Company | null>(null);
  const [tools, setTools] = useState<ToolDefinition[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [executions, setExecutions] = useState<ToolExecutionRecord[]>([]);
  const [selectedExecution, setSelectedExecution] = useState<ToolExecutionRecord | null>(null);

  // Runner state
  const [selectedAgentId, setSelectedAgentId] = useState<string>("");
  const [selectedToolName, setSelectedToolName] = useState<string>("web_search");
  const [actionInput, setActionInput] = useState<string>("search");
  const [parametersJson, setParametersJson] = useState<string>(
    JSON.stringify({ query: "best practices for bounded AI agent execution", max_results: 3 }, null, 2)
  );
  const [executing, setExecuting] = useState(false);
  const [latestResult, setLatestResult] = useState<ToolExecutionRecord | null>(null);
  const [runnerError, setRunnerError] = useState<string | null>(null);

  // Filters & Loading
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [toolFilter, setToolFilter] = useState<string>("all");
  const [activeTab, setActiveTab] = useState<"registry" | "runner" | "audit">("registry");

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
        await loadCompanyData(primary.id);
      }
    } catch (err) {
      console.error("Failed loading company list:", err);
    } finally {
      setLoading(false);
    }
  }

  async function loadCompanyData(companyId: string) {
    setRefreshing(true);
    try {
      const [toolsResp, agentsList, execsResp] = await Promise.all([
        api.getTools(companyId).catch(() => ({ items: [], total: 0 })),
        api.getAgents(companyId).catch(() => []),
        api.getToolExecutions(companyId, { limit: 50 }).catch(() => ({ items: [], total: 0 })),
      ]);
      setTools(toolsResp.items);
      setAgents(agentsList);
      setExecutions(execsResp.items);

      if (agentsList.length > 0 && !selectedAgentId) {
        // Select an engineering agent or the first available
        const eng = agentsList.find((a) =>
          a.role.toLowerCase().includes("engineer") || a.role.toLowerCase().includes("backend")
        );
        setSelectedAgentId(eng ? eng.id : agentsList[0].id);
      }
    } catch (err) {
      console.error("Failed loading company tools data:", err);
    } finally {
      setRefreshing(false);
    }
  }

  function applyPreset(toolName: string, action: string, params: Record<string, unknown>) {
    setSelectedToolName(toolName);
    setActionInput(action);
    setParametersJson(JSON.stringify(params, null, 2));
    setRunnerError(null);
  }

  async function handleExecute() {
    if (!activeCompany) return;
    if (!selectedAgentId) {
      setRunnerError("Please select a calling agent.");
      return;
    }

    let parsedParams: Record<string, unknown> = {};
    try {
      parsedParams = JSON.parse(parametersJson);
    } catch (err) {
      setRunnerError("Invalid JSON in parameters field: " + String(err));
      return;
    }

    setExecuting(true);
    setRunnerError(null);
    try {
      const record = await api.executeTool(activeCompany.id, {
        agent_id: selectedAgentId,
        tool_name: selectedToolName,
        action: actionInput || "default",
        parameters: parsedParams,
      });
      setLatestResult(record);
      // Refresh audit logs
      const updatedExecs = await api.getToolExecutions(activeCompany.id, { limit: 50 });
      setExecutions(updatedExecs.items);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setRunnerError(msg);
    } finally {
      setExecuting(false);
    }
  }

  const filteredExecutions = executions.filter((e) => {
    if (statusFilter !== "all" && e.status !== statusFilter) return false;
    if (toolFilter !== "all" && e.tool_name !== toolFilter) return false;
    return true;
  });

  const getToolIcon = (name: string) => {
    switch (name.toLowerCase()) {
      case "web_search":
        return <Globe className="w-5 h-5 text-sky-400" />;
      case "documents":
        return <FileText className="w-5 h-5 text-amber-400" />;
      case "github":
        return <Github className="w-5 h-5 text-purple-400" />;
      default:
        return <Wrench className="w-5 h-5 text-indigo-400" />;
    }
  };

  const getRiskBadge = (level: string) => {
    switch (level?.toUpperCase()) {
      case "LOW":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <ShieldCheck className="w-3 h-3" /> LOW RISK
          </span>
        );
      case "MEDIUM":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Shield className="w-3 h-3" /> MEDIUM RISK
          </span>
        );
      case "HIGH":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-orange-500/10 text-orange-400 border border-orange-500/20">
            <ShieldAlert className="w-3 h-3" /> HIGH RISK
          </span>
        );
      case "CRITICAL":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertTriangle className="w-3 h-3" /> CRITICAL
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-400">
            {level}
          </span>
        );
    }
  };

  const getStatusBadge = (status: string, requiresApproval: boolean) => {
    if (status === "APPROVAL_REQUIRED" || requiresApproval) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse">
          <Clock className="w-3.5 h-3.5" /> APPROVAL REQUIRED
        </span>
      );
    }
    if (status === "SUCCESS") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-3.5 h-3.5" /> SUCCESS
        </span>
      );
    }
    if (status === "FAILED") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <AlertCircle className="w-3.5 h-3.5" /> FAILED
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
        {status}
      </span>
    );
  };

  return (
    <ShellLayout pageTitle="Tool Gateway" breadcrumb="Work Management">
      <div className="space-y-6 pb-12">
        {/* Header Banner */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-[#1e2738] pb-6">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                <Wrench className="w-6 h-6 text-indigo-400" />
                Tool Gateway
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Phase 9 Active
              </span>
            </div>
            <p className="text-sm text-slate-400 max-w-2xl">
              Controlled access to external capabilities. Enforces schema validation, role permissions,
              risk classification, secret sanitization, and immutable audit logging.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {activeCompany && (
              <button
                onClick={() => loadCompanyData(activeCompany.id)}
                disabled={refreshing}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[#1e2738] bg-[#111724] hover:bg-[#182030] text-xs font-medium text-slate-300 hover:text-white transition disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-indigo-400" : ""}`} />
                <span>Refresh Tools</span>
              </button>
            )}
          </div>
        </div>

        {/* Phase Rules & Presence Disclaimer */}
        <div className="rounded-xl border border-indigo-500/20 bg-gradient-to-r from-indigo-500/10 via-purple-500/5 to-transparent p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
          <div className="flex items-start md:items-center gap-2.5">
            <Shield className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5 md:mt-0" />
            <div className="text-slate-300">
              <strong className="text-white font-semibold">Security Boundary:</strong> All agent calls pass
              through the 8-step Tool Gateway. Actions requiring human approval are halted as{" "}
              <code className="text-amber-300 bg-amber-950/40 px-1 py-0.5 rounded font-mono">APPROVAL_REQUIRED</code>{" "}
              pending Phase 10 operator review.
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-400 font-mono text-[11px] border border-slate-700">
              Active Agents: 0 (Phase 14)
            </span>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 border-b border-[#1e2738]">
          <button
            onClick={() => setActiveTab("registry")}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "registry"
                ? "border-indigo-500 text-white"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Tool Registry ({tools.length})</span>
          </button>
          <button
            onClick={() => setActiveTab("runner")}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "runner"
                ? "border-indigo-500 text-white"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Play className="w-4 h-4" />
            <span>Interactive Runner</span>
          </button>
          <button
            onClick={() => setActiveTab("audit")}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "audit"
                ? "border-indigo-500 text-white"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Terminal className="w-4 h-4" />
            <span>Audit Trail ({executions.length})</span>
          </button>
        </div>

        {/* TAB 1: TOOL REGISTRY */}
        {activeTab === "registry" && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {tools.map((tool) => (
                <div
                  key={tool.name}
                  className="rounded-xl border border-[#1e2738] bg-[#111724] p-5 flex flex-col justify-between hover:border-slate-700 transition-colors"
                >
                  <div>
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-lg bg-[#0c1017] border border-[#1e2738]">
                          {getToolIcon(tool.name)}
                        </div>
                        <div>
                          <h3 className="text-base font-semibold text-white">{tool.name}</h3>
                          <span className="text-[11px] font-mono text-slate-400">v{tool.version} · {tool.provider}</span>
                        </div>
                      </div>
                      {getRiskBadge(tool.risk_level)}
                    </div>

                    <p className="text-xs text-slate-300 mb-4 leading-relaxed">
                      {tool.description}
                    </p>

                    <div className="space-y-2 mb-4 text-xs">
                      <div className="flex items-center justify-between text-slate-400">
                        <span>Approval Mandated:</span>
                        <span className={tool.requires_approval ? "text-amber-400 font-semibold" : "text-slate-300"}>
                          {tool.requires_approval ? "Yes (Always)" : "Risk-dependent"}
                        </span>
                      </div>
                      <div className="text-slate-400">
                        <span className="block mb-1">Permitted Roles:</span>
                        <div className="flex flex-wrap gap-1">
                          {tool.allowed_roles.map((role) => (
                            <span
                              key={role}
                              className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700"
                            >
                              {role === "*" ? "All Roles (*)" : role}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      setSelectedToolName(tool.name);
                      if (tool.name === "web_search") {
                        applyPreset("web_search", "search", { query: "fastapi microservices", max_results: 3 });
                      } else if (tool.name === "documents") {
                        applyPreset("documents", "read", { document_id: "architecture_spec" });
                      } else if (tool.name === "github") {
                        applyPreset("github", "inspect_repo", { repository: "moon90/AICompanyOS", action: "inspect_repo" });
                      }
                      setActiveTab("runner");
                    }}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-[#0c1017] hover:bg-[#182030] border border-[#1e2738] text-xs font-medium text-slate-300 hover:text-white transition"
                  >
                    <Play className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Test In Runner</span>
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 2: INTERACTIVE RUNNER */}
        {activeTab === "runner" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Form */}
            <div className="rounded-xl border border-[#1e2738] bg-[#111724] p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#1e2738]">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Play className="w-4 h-4 text-indigo-400" />
                  Tool Execution Parameters
                </h3>
                <span className="text-xs text-slate-400 font-mono">8-step pipeline</span>
              </div>

              {/* Quick Presets */}
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">Preset Scenarios</label>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => applyPreset("web_search", "search", { query: "best practices for bounded AI agent execution", max_results: 3 })}
                    className="px-2.5 py-1 rounded bg-[#0c1017] hover:bg-[#182030] border border-[#1e2738] text-xs text-slate-300 hover:text-white transition"
                  >
                    Web: Agent Best Practices
                  </button>
                  <button
                    type="button"
                    onClick={() => applyPreset("documents", "read", { document_id: "architecture_spec" })}
                    className="px-2.5 py-1 rounded bg-[#0c1017] hover:bg-[#182030] border border-[#1e2738] text-xs text-slate-300 hover:text-white transition"
                  >
                    Docs: Architecture Spec
                  </button>
                  <button
                    type="button"
                    onClick={() => applyPreset("documents", "read", { document_id: "security_guidelines" })}
                    className="px-2.5 py-1 rounded bg-[#0c1017] hover:bg-[#182030] border border-[#1e2738] text-xs text-slate-300 hover:text-white transition"
                  >
                    Docs: Security Guidelines
                  </button>
                  <button
                    type="button"
                    onClick={() => applyPreset("github", "inspect_repo", { repository: "moon90/AICompanyOS", action: "inspect_repo" })}
                    className="px-2.5 py-1 rounded bg-[#0c1017] hover:bg-[#182030] border border-[#1e2738] text-xs text-slate-300 hover:text-white transition"
                  >
                    GitHub: Inspect Repo
                  </button>
                  <button
                    type="button"
                    onClick={() => applyPreset("github", "create_pr", { repository: "moon90/AICompanyOS", action: "create_pr", branch: "main" })}
                    className="px-2.5 py-1 rounded bg-amber-950/40 hover:bg-amber-900/50 border border-amber-600/30 text-xs text-amber-300 transition flex items-center gap-1"
                  >
                    <ShieldAlert className="w-3 h-3 text-amber-400" />
                    GitHub: High Risk (Approval Demo)
                  </button>
                </div>
              </div>

              {/* Calling Agent */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Calling Agent Identity (Authority & Permissions)
                </label>
                <select
                  value={selectedAgentId}
                  onChange={(e) => setSelectedAgentId(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  {agents.map((ag) => (
                    <option key={ag.id} value={ag.id}>
                      {ag.name} ({ag.role} · {ag.status})
                    </option>
                  ))}
                </select>
              </div>

              {/* Target Tool */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Registered Tool</label>
                  <select
                    value={selectedToolName}
                    onChange={(e) => {
                      const name = e.target.value;
                      setSelectedToolName(name);
                      if (name === "web_search") {
                        applyPreset("web_search", "search", { query: "modern system architectures", max_results: 3 });
                      } else if (name === "documents") {
                        applyPreset("documents", "read", { document_id: "architecture_spec" });
                      } else if (name === "github") {
                        applyPreset("github", "inspect_repo", { repository: "moon90/AICompanyOS", action: "inspect_repo" });
                      }
                    }}
                    className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                    {tools.map((t) => (
                      <option key={t.name} value={t.name}>
                        {t.name} ({t.risk_level})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Action / Method</label>
                  <input
                    type="text"
                    value={actionInput}
                    onChange={(e) => setActionInput(e.target.value)}
                    placeholder="e.g. search, read, inspect_repo"
                    className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* JSON Parameters */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Input Parameters (JSON Schema Validated & Secrets Stripped)
                </label>
                <textarea
                  rows={6}
                  value={parametersJson}
                  onChange={(e) => setParametersJson(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              {runnerError && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{runnerError}</span>
                </div>
              )}

              <button
                type="button"
                onClick={handleExecute}
                disabled={executing}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-sm font-semibold text-white transition disabled:opacity-50"
              >
                {executing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Executing Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    <span>Execute via Tool Gateway</span>
                  </>
                )}
              </button>
            </div>

            {/* Execution Result View */}
            <div className="rounded-xl border border-[#1e2738] bg-[#111724] p-5 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-[#1e2738] mb-4">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-emerald-400" />
                    Gateway Output & Telemetry
                  </h3>
                  {latestResult && getStatusBadge(latestResult.status, latestResult.requires_approval)}
                </div>

                {!latestResult ? (
                  <div className="flex flex-col items-center justify-center py-16 text-center text-slate-500">
                    <Terminal className="w-10 h-10 mb-3 opacity-40" />
                    <p className="text-sm font-medium text-slate-400">No Invocation Yet</p>
                    <p className="text-xs max-w-xs mt-1">
                      Choose an agent and tool parameters on the left to trigger a validated Tool Gateway invocation.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Execution Meta */}
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div className="p-2.5 rounded-lg bg-[#0c1017] border border-[#1e2738]">
                        <span className="text-slate-400 block text-[10px]">Risk Tier</span>
                        {getRiskBadge(latestResult.risk_level)}
                      </div>
                      <div className="p-2.5 rounded-lg bg-[#0c1017] border border-[#1e2738]">
                        <span className="text-slate-400 block text-[10px]">Duration</span>
                        <span className="font-mono text-white font-semibold">{latestResult.duration_ms} ms</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-[#0c1017] border border-[#1e2738]">
                        <span className="text-slate-400 block text-[10px]">Audit Record ID</span>
                        <span className="font-mono text-slate-300 truncate block text-[11px]" title={latestResult.id}>
                          {latestResult.id.slice(0, 8)}...
                        </span>
                      </div>
                    </div>

                    {/* Approval Notice if APPROVAL_REQUIRED */}
                    {latestResult.requires_approval && (
                      <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-start gap-2.5">
                        <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                        <div>
                          <strong className="text-white block font-semibold mb-0.5">
                            Action Intercepted: Approval Gate Triggered
                          </strong>
                          <span>{latestResult.error_details}</span>
                          <span className="block mt-1 text-slate-400 text-[11px]">
                            Phase 10 will provide the operator approval review and release queue.
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Normalized Output */}
                    <div>
                      <span className="block text-xs font-medium text-slate-400 mb-1">
                        Normalized Domain Output:
                      </span>
                      <pre className="p-3 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs font-mono text-emerald-400 overflow-x-auto max-h-72">
                        {JSON.stringify(latestResult.output_data, null, 2)}
                      </pre>
                    </div>

                    {/* Sanitized Inputs */}
                    <div>
                      <span className="block text-xs font-medium text-slate-400 mb-1">
                        Sanitized Input Parameters (Audit-Logged):
                      </span>
                      <pre className="p-3 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs font-mono text-slate-400 overflow-x-auto max-h-36">
                        {JSON.stringify(latestResult.input_params, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: AUDIT TRAIL */}
        {activeTab === "audit" && (
          <div className="rounded-xl border border-[#1e2738] bg-[#111724] p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#1e2738]">
              <div>
                <h3 className="text-sm font-semibold text-white">Immutable Tool Execution Audit Log</h3>
                <p className="text-xs text-slate-400">
                  Every tool invocation is recorded with sanitized inputs, risk classifications, and duration metrics.
                </p>
              </div>

              {/* Filters */}
              <div className="flex items-center gap-2">
                <select
                  value={toolFilter}
                  onChange={(e) => setToolFilter(e.target.value)}
                  className="px-2.5 py-1.5 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs text-slate-300 focus:outline-none"
                >
                  <option value="all">All Tools</option>
                  <option value="web_search">web_search</option>
                  <option value="documents">documents</option>
                  <option value="github">github</option>
                </select>

                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-2.5 py-1.5 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs text-slate-300 focus:outline-none"
                >
                  <option value="all">All Statuses</option>
                  <option value="SUCCESS">SUCCESS</option>
                  <option value="APPROVAL_REQUIRED">APPROVAL_REQUIRED</option>
                  <option value="FAILED">FAILED</option>
                </select>
              </div>
            </div>

            {filteredExecutions.length === 0 ? (
              <div className="py-12 text-center text-slate-500">
                <Terminal className="w-8 h-8 mx-auto mb-2 opacity-40" />
                <p className="text-sm text-slate-400">No tool execution logs found.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="text-[11px] uppercase tracking-wider text-slate-400 bg-[#0c1017] border-b border-[#1e2738]">
                    <tr>
                      <th className="py-2.5 px-3">Timestamp</th>
                      <th className="py-2.5 px-3">Tool</th>
                      <th className="py-2.5 px-3">Action</th>
                      <th className="py-2.5 px-3">Risk</th>
                      <th className="py-2.5 px-3">Duration</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3 text-right">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1e2738] text-slate-300">
                    {filteredExecutions.map((item) => (
                      <tr key={item.id} className="hover:bg-[#182030]/50 transition-colors">
                        <td className="py-3 px-3 font-mono text-slate-400">
                          {new Date(item.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                        </td>
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-2">
                            {getToolIcon(item.tool_name)}
                            <span className="font-semibold text-white">{item.tool_name}</span>
                          </div>
                        </td>
                        <td className="py-3 px-3 font-mono text-slate-300">{item.action}</td>
                        <td className="py-3 px-3">{getRiskBadge(item.risk_level)}</td>
                        <td className="py-3 px-3 font-mono text-slate-400">{item.duration_ms} ms</td>
                        <td className="py-3 px-3">
                          {getStatusBadge(item.status, item.requires_approval)}
                        </td>
                        <td className="py-3 px-3 text-right">
                          <button
                            onClick={() => setSelectedExecution(item)}
                            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition"
                            title="Inspect Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Audit Details Modal */}
        {selectedExecution && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#111724] border border-[#1e2738] rounded-xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl">
              <div className="p-4 border-b border-[#1e2738] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getToolIcon(selectedExecution.tool_name)}
                  <h3 className="text-base font-bold text-white">
                    Execution: {selectedExecution.tool_name} ({selectedExecution.action})
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedExecution(null)}
                  className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-5 overflow-y-auto space-y-4 text-xs">
                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2.5 rounded-lg bg-[#0c1017] border border-[#1e2738]">
                    <span className="text-slate-400 block text-[10px]">Status</span>
                    {getStatusBadge(selectedExecution.status, selectedExecution.requires_approval)}
                  </div>
                  <div className="p-2.5 rounded-lg bg-[#0c1017] border border-[#1e2738]">
                    <span className="text-slate-400 block text-[10px]">Risk Level</span>
                    {getRiskBadge(selectedExecution.risk_level)}
                  </div>
                  <div className="p-2.5 rounded-lg bg-[#0c1017] border border-[#1e2738]">
                    <span className="text-slate-400 block text-[10px]">Duration</span>
                    <span className="font-mono text-white">{selectedExecution.duration_ms} ms</span>
                  </div>
                </div>

                {selectedExecution.error_details && (
                  <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300">
                    <strong className="block text-white font-semibold mb-1">Details / Approval Notice:</strong>
                    <span>{selectedExecution.error_details}</span>
                  </div>
                )}

                <div>
                  <span className="block text-xs font-semibold text-slate-300 mb-1">
                    Normalized Output Data:
                  </span>
                  <pre className="p-3 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs font-mono text-emerald-400 overflow-x-auto max-h-56">
                    {JSON.stringify(selectedExecution.output_data, null, 2)}
                  </pre>
                </div>

                <div>
                  <span className="block text-xs font-semibold text-slate-300 mb-1">
                    Sanitized Parameters:
                  </span>
                  <pre className="p-3 rounded-lg bg-[#0c1017] border border-[#1e2738] text-xs font-mono text-slate-400 overflow-x-auto max-h-40">
                    {JSON.stringify(selectedExecution.input_params, null, 2)}
                  </pre>
                </div>
              </div>

              <div className="p-4 border-t border-[#1e2738] flex justify-end">
                <button
                  onClick={() => setSelectedExecution(null)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-white transition"
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
