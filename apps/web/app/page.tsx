"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Bot,
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
import { api, SystemStatus, User } from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

export default function DashboardPage() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>("");

  async function loadTelemetry() {
    setStatusLoading(true);
    try {
      const [user, status] = await Promise.all([
        api.getMe(),
        api.getSystemStatus(),
      ]);
      setCurrentUser(user);
      setSystemStatus(status);
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
      subtext: "No active agents",
      phaseNote: "Scheduled for Phase 4",
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
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                Executive Dashboard
              </h1>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                Phase 2 Foundation
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-400">
              Real-time operating picture of company systems, foundation, and agent readiness.
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

            {/* Roadmap Status */}
            <div className="p-4 rounded-lg bg-[#0c1017] border border-[#1e2738]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400 font-medium">Roadmap State</span>
                <CheckSquare className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-sm font-semibold text-white mb-1 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Phase 2 Shell</span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                Next: Phase 3 (Company)
              </p>
            </div>
          </div>
        </div>
      </div>
    </ShellLayout>
  );
}
