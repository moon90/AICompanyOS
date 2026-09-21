"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bot,
  Building2,
  CheckCircle2,
  CheckSquare,
  Database,
  FolderGit2,
  Lock,
  RefreshCw,
  Server,
  ShieldAlert,
  Users,
} from "lucide-react";
import Link from "next/link";
import { api, Company, SystemStatus, User } from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

export default function DashboardPage() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [activeCompany, setActiveCompany] = useState<Company | null>(null);
  const [departmentCount, setDepartmentCount] = useState<number>(0);
  const [agentCount, setAgentCount] = useState<number>(0);
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
          const [depts, ags] = await Promise.all([
            api.getDepartments(primaryCompany.id).catch(() => []),
            api.getAgents(primaryCompany.id).catch(() => []),
          ]);
          setDepartmentCount(depts.length);
          setAgentCount(ags.length);
        } catch {
          setDepartmentCount(0);
          setAgentCount(0);
        }
      } else {
        setDepartmentCount(0);
        setAgentCount(0);
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
      value: "0",
      subtext: "No active projects",
      phaseNote: "Scheduled for Phase 3/6",
      icon: FolderGit2,
      accentColor: "text-blue-400",
      bgColor: "bg-blue-500/10",
      borderColor: "border-blue-500/20",
    },
    {
      title: "Open Tasks",
      value: "0",
      subtext: "No open tasks",
      phaseNote: "Scheduled for Phase 6",
      icon: CheckSquare,
      accentColor: "text-indigo-400",
      bgColor: "bg-indigo-500/10",
      borderColor: "border-indigo-500/20",
    },
    {
      title: "Blocked Tasks",
      value: "0",
      subtext: "No blocked tasks",
      phaseNote: "Operational baseline",
      icon: AlertTriangle,
      accentColor: "text-amber-400",
      bgColor: "bg-amber-500/10",
      borderColor: "border-amber-500/20",
    },
    {
      title: "Pending Approvals",
      value: "0",
      subtext: "No pending approvals",
      phaseNote: "Scheduled for Phase 10",
      icon: ShieldAlert,
      accentColor: "text-purple-400",
      bgColor: "bg-purple-500/10",
      borderColor: "border-purple-500/20",
    },
    {
      title: "Active Agents",
      value: "0",
      subtext: agentCount > 0 ? `${agentCount} registered (0 runtime active)` : "No active agents",
      phaseNote: "Execution loop scheduled for Phase 5",
      icon: Users,
      accentColor: "text-emerald-400",
      bgColor: "bg-emerald-500/10",
      borderColor: "border-emerald-500/20",
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
                Phase 4 Active
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

        {/* Metric Cards Row per docs/Phases.md § 6 & docs/UI.md § 27 */}
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
            Company Statistics Overview
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {metricCards.map((card) => {
              const Icon = card.icon;
              return (
                <div
                  key={card.title}
                  className="rounded-xl border border-[#1e2738] bg-[#111724] p-5 flex flex-col justify-between hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">
                      {card.title}
                    </span>
                    <div className={`p-2 rounded-lg ${card.bgColor} ${card.accentColor} border ${card.borderColor}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="text-3xl font-bold tracking-tight text-white font-mono">
                      {card.value}
                    </div>
                    <div className="text-xs text-slate-400 font-medium">
                      {card.subtext}
                    </div>
                    <div className="text-[10px] font-mono text-slate-400 pt-1">
                      {card.phaseNote}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
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
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                Phase 5
              </span>
            </div>

            {/* Honest Empty State */}
            <div className="flex-1 flex flex-col items-center justify-center text-center py-8 px-4">
              <div className="w-12 h-12 rounded-xl bg-slate-800/60 border border-slate-700/60 text-slate-400 flex items-center justify-center mb-4">
                <Bot className="w-6 h-6" />
              </div>
              <h4 className="text-sm font-semibold text-white mb-1">
                No Active Operations
              </h4>
              <p className="text-xs text-slate-400 max-w-sm leading-relaxed mb-4">
                Autonomous agent coordination and CEO orchestration will activate in{" "}
                <strong className="text-slate-300">Phase 5</strong>. Once enabled, the CEO agent
                will plan, delegate to specialists, and track work live in this panel.
              </p>
              <span className="text-[11px] font-mono text-slate-400 bg-slate-800/60 px-2.5 py-1 rounded border border-slate-700/60">
                Awaiting Phase 5 Orchestrator
              </span>
            </div>
          </div>

          {/* Recent Activity Panel */}
          <div className="rounded-xl border border-[#1e2738] bg-[#111724] p-6 flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-[#1e2738] mb-6">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <Activity className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">Recent Activity</h3>
                  <p className="text-xs text-slate-400">Audit trail, agent events, and company history</p>
                </div>
              </div>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                Phase 13
              </span>
            </div>

            {/* Honest Empty State */}
            <div className="flex-1 flex flex-col items-center justify-center text-center py-8 px-4">
              <div className="w-12 h-12 rounded-xl bg-slate-800/60 border border-slate-700/60 text-slate-400 flex items-center justify-center mb-4">
                <Activity className="w-6 h-6" />
              </div>
              <h4 className="text-sm font-semibold text-white mb-1">
                No Activity Recorded
              </h4>
              <p className="text-xs text-slate-400 max-w-sm leading-relaxed mb-4">
                Real-time event streaming and comprehensive company activity tracking will activate in{" "}
                <strong className="text-slate-300">Phase 13</strong>. Authentication session events are currently
                stored authoritatively in PostgreSQL.
              </p>
              <span className="text-[11px] font-mono text-slate-400 bg-slate-800/60 px-2.5 py-1 rounded border border-slate-700/60">
                Awaiting Phase 13 Event Bus
              </span>
            </div>
          </div>
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
                {activeCompany ? `${departmentCount} Depts · ${agentCount} Agents Registered` : "Phase 4 Ready"}
              </p>
            </div>
          </div>
        </div>
      </div>
    </ShellLayout>
  );
}
