"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  FolderGit2,
  Layers,
  ListTodo,
  Loader2,
  Plus,
  Search,
  SlidersHorizontal,
  Trash2,
  X,
} from "lucide-react";
import { api, Company, Project } from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string; border: string }> = {
  PLANNED: { label: "Planned", bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/20" },
  ACTIVE: { label: "Active", bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/20" },
  BLOCKED: { label: "Blocked", bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/20" },
  COMPLETED: { label: "Completed", bg: "bg-purple-500/10", text: "text-purple-400", border: "border-purple-500/20" },
  CANCELLED: { label: "Cancelled", bg: "bg-zinc-500/10", text: "text-zinc-400", border: "border-zinc-500/20" },
};

const PRIORITY_CONFIG: Record<string, { label: string; text: string }> = {
  low: { label: "Low", text: "text-zinc-400" },
  medium: { label: "Medium", text: "text-blue-400" },
  high: { label: "High", text: "text-amber-400" },
  critical: { label: "Critical", text: "text-rose-400 font-semibold" },
};

export default function ProjectsPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [activeCompany, setActiveCompany] = useState<Company | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [totalProjects, setTotalProjects] = useState(0);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [priorityFilter, setPriorityFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Loading & Error
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals & Detail
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [createSubmitting, setCreateSubmitting] = useState(false);

  // Create Form State
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newObjective, setNewObjective] = useState("");
  const [newPriority, setNewPriority] = useState("medium");
  const [newStatus, setNewStatus] = useState("PLANNED");

  // Load Companies
  useEffect(() => {
    async function loadCompanies() {
      try {
        const comps = await api.getCompanies();
        setCompanies(comps);
        if (comps.length > 0) {
          setActiveCompany(comps[0]);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load companies");
      } finally {
        setLoading(false);
      }
    }
    loadCompanies();
  }, []);

  // Load Projects
  const loadProjects = useCallback(async () => {
    if (!activeCompany) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.getProjects(activeCompany.id, {
        status: statusFilter !== "ALL" ? statusFilter : undefined,
        priority: priorityFilter !== "ALL" ? priorityFilter : undefined,
        search: searchQuery.trim() || undefined,
      });
      setProjects(res.items);
      setTotalProjects(res.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to fetch projects");
    } finally {
      setLoading(false);
    }
  }, [activeCompany, statusFilter, priorityFilter, searchQuery]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  // Handle Create Project
  async function handleCreateProject(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompany || !newName.trim()) return;

    setCreateSubmitting(true);
    try {
      await api.createProject(activeCompany.id, {
        name: newName.trim(),
        description: newDescription.trim() || undefined,
        objective: newObjective.trim() || undefined,
        priority: newPriority,
        status: newStatus,
      });
      setShowCreateModal(false);
      setNewName("");
      setNewDescription("");
      setNewObjective("");
      setNewPriority("medium");
      setNewStatus("PLANNED");
      await loadProjects();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setCreateSubmitting(false);
    }
  }

  // Handle Delete Project
  async function handleDeleteProject(projectId: string) {
    if (!activeCompany || !confirm("Are you sure you want to delete this project? Associated tasks will be deleted.")) return;
    try {
      await api.deleteProject(activeCompany.id, projectId);
      if (selectedProject?.id === projectId) {
        setSelectedProject(null);
      }
      await loadProjects();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete project");
    }
  }

  // Handle Update Status
  async function handleStatusChange(projectId: string, nextStatus: string) {
    if (!activeCompany) return;
    try {
      const updated = await api.updateProject(activeCompany.id, projectId, { status: nextStatus });
      setSelectedProject(updated);
      await loadProjects();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update status");
    }
  }

  return (
    <ShellLayout pageTitle="Projects" breadcrumb="Work Management">
      <div className="space-y-6">
        {/* Top Controls Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-zinc-900/50 p-4 rounded-xl border border-zinc-800">
          <div>
            <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
              <FolderGit2 className="h-6 w-6 text-blue-400" />
              Project Portfolio
            </h1>
            <p className="text-sm text-zinc-400 mt-1">
              Persistent cross-department initiatives, objectives, and work breakdown milestones.
            </p>
          </div>
          <div className="flex items-center gap-3">
            {companies.length > 1 && (
              <select
                value={activeCompany?.id || ""}
                onChange={(e) => {
                  const comp = companies.find((c) => c.id === e.target.value);
                  if (comp) setActiveCompany(comp);
                }}
                className="bg-zinc-800 border border-zinc-700 text-zinc-200 text-sm rounded-lg px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            )}
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors shadow-sm"
            >
              <Plus className="h-4 w-4" />
              New Project
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-rose-400 text-sm">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <span className="flex-1">{error}</span>
            <button onClick={() => setError(null)} className="text-rose-400 hover:text-rose-300">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Filters & Search */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
            <input
              type="text"
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-zinc-900/60 border border-zinc-800 rounded-lg text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <SlidersHorizontal className="h-4 w-4 text-zinc-500 shrink-0" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full py-2 px-3 bg-zinc-900/60 border border-zinc-800 rounded-lg text-sm text-zinc-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="PLANNED">Planned</option>
              <option value="ACTIVE">Active</option>
              <option value="BLOCKED">Blocked</option>
              <option value="COMPLETED">Completed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          <div>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="w-full py-2 px-3 bg-zinc-900/60 border border-zinc-800 rounded-lg text-sm text-zinc-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="ALL">All Priorities</option>
              <option value="low">Low Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="high">High Priority</option>
              <option value="critical">Critical Priority</option>
            </select>
          </div>
        </div>

        {/* Status Rollup Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {["PLANNED", "ACTIVE", "BLOCKED", "COMPLETED", "CANCELLED"].map((st) => {
            const cfg = STATUS_CONFIG[st];
            const count = projects.filter((p) => p.status === st).length;
            const isSelected = statusFilter === st;
            return (
              <button
                key={st}
                onClick={() => setStatusFilter(isSelected ? "ALL" : st)}
                className={`p-3 rounded-lg border text-left transition-all ${
                  isSelected
                    ? `${cfg.bg} ${cfg.border} ring-1 ring-blue-500/50`
                    : "bg-zinc-900/40 border-zinc-800 hover:border-zinc-700"
                }`}
              >
                <span className="text-xs text-zinc-500 uppercase tracking-wider block font-medium">
                  {cfg.label}
                </span>
                <span className={`text-xl font-bold mt-1 block ${cfg.text}`}>{count}</span>
              </button>
            );
          })}
        </div>

        {/* Projects Grid / List */}
        {loading ? (
          <div className="py-16 flex flex-col items-center justify-center text-zinc-500 gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            <span className="text-sm">Loading project portfolio...</span>
          </div>
        ) : projects.length === 0 ? (
          <div className="py-16 text-center bg-zinc-900/30 border border-zinc-800/80 rounded-2xl p-8">
            <FolderGit2 className="h-12 w-12 text-zinc-600 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-zinc-300">No projects found</h3>
            <p className="text-sm text-zinc-500 mt-1 max-w-sm mx-auto">
              {searchQuery || statusFilter !== "ALL" || priorityFilter !== "ALL"
                ? "No projects match your active search filters."
                : "Initiate strategic cross-functional projects to group tasks and drive execution."}
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg inline-flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Create First Project
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => {
              const statusCfg = STATUS_CONFIG[project.status] || STATUS_CONFIG.PLANNED;
              const priorityCfg = PRIORITY_CONFIG[project.priority] || PRIORITY_CONFIG.medium;
              const stats = project.stats;
              const progressPct =
                stats && stats.total_tasks > 0
                  ? Math.round((stats.completed_tasks / stats.total_tasks) * 100)
                  : 0;

              return (
                <div
                  key={project.id}
                  onClick={() => setSelectedProject(project)}
                  className="bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700 rounded-xl p-5 cursor-pointer transition-all hover:shadow-lg flex flex-col justify-between group"
                >
                  <div>
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-medium border ${statusCfg.bg} ${statusCfg.text} ${statusCfg.border}`}
                      >
                        {statusCfg.label}
                      </span>
                      <span className={`text-xs uppercase tracking-wider ${priorityCfg.text}`}>
                        {priorityCfg.label}
                      </span>
                    </div>

                    {/* Title & Description */}
                    <h3 className="text-base font-semibold text-zinc-100 group-hover:text-blue-400 transition-colors">
                      {project.name}
                    </h3>
                    {project.description && (
                      <p className="text-xs text-zinc-400 mt-1.5 line-clamp-2 leading-relaxed">
                        {project.description}
                      </p>
                    )}
                    {project.objective && (
                      <div className="mt-2.5 p-2 bg-zinc-800/40 rounded border border-zinc-800 text-xs text-zinc-300">
                        <span className="text-zinc-500 font-medium block text-[10px] uppercase tracking-wider">
                          Objective
                        </span>
                        <span className="line-clamp-2">{project.objective}</span>
                      </div>
                    )}
                  </div>

                  {/* Task Progress Rollup */}
                  <div className="mt-5 pt-4 border-t border-zinc-800/80">
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="text-zinc-400 flex items-center gap-1.5">
                        <ListTodo className="h-3.5 w-3.5 text-zinc-500" />
                        Progress
                      </span>
                      <span className="text-zinc-200 font-medium">{progressPct}%</span>
                    </div>
                    <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-blue-500 h-full rounded-full transition-all duration-300"
                        style={{ width: `${progressPct}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-zinc-500 mt-2">
                      <span>{stats?.total_tasks || 0} total tasks</span>
                      <Link
                        href={`/projects/${project.id}/board`}
                        onClick={(e) => e.stopPropagation()}
                        className="text-primary hover:text-primary-hover font-medium flex items-center gap-1 group-hover:underline"
                      >
                        <Layers className="h-3 w-3" />
                        Board →
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Project Detail Drawer */}
        {selectedProject && (
          <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-in fade-in">
            <div className="w-full max-w-lg bg-zinc-900 border-l border-zinc-800 h-full overflow-y-auto p-6 flex flex-col justify-between shadow-2xl">
              <div className="space-y-6">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-medium border ${
                          (STATUS_CONFIG[selectedProject.status] || STATUS_CONFIG.PLANNED).bg
                        } ${(STATUS_CONFIG[selectedProject.status] || STATUS_CONFIG.PLANNED).text} ${
                          (STATUS_CONFIG[selectedProject.status] || STATUS_CONFIG.PLANNED).border
                        }`}
                      >
                        {selectedProject.status}
                      </span>
                      <span className="text-xs text-zinc-400 capitalize">
                        Priority: {selectedProject.priority}
                      </span>
                    </div>
                    <h2 className="text-xl font-bold text-zinc-100">{selectedProject.name}</h2>
                  </div>
                  <button
                    onClick={() => setSelectedProject(null)}
                    className="p-1 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                {/* Status Transition Bar */}
                <div className="p-4 bg-zinc-800/40 rounded-xl border border-zinc-800 space-y-2">
                  <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block">
                    Change Project Status
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {["PLANNED", "ACTIVE", "BLOCKED", "COMPLETED", "CANCELLED"].map((st) => (
                      <button
                        key={st}
                        onClick={() => handleStatusChange(selectedProject.id, st)}
                        className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-all ${
                          selectedProject.status === st
                            ? "bg-blue-600 border-blue-500 text-white"
                            : "bg-zinc-900 border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                        }`}
                      >
                        {st}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Objective & Description */}
                {selectedProject.objective && (
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
                      Strategic Objective
                    </h4>
                    <p className="text-sm text-zinc-200 bg-zinc-950 p-3 rounded-lg border border-zinc-800">
                      {selectedProject.objective}
                    </p>
                  </div>
                )}

                {selectedProject.description && (
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
                      Description
                    </h4>
                    <p className="text-sm text-zinc-300 leading-relaxed">
                      {selectedProject.description}
                    </p>
                  </div>
                )}

                {/* Task Rollup Breakdown */}
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                    <Layers className="h-4 w-4 text-blue-400" />
                    Task Rollup
                  </h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-zinc-950 rounded-lg border border-zinc-800">
                      <span className="text-xs text-zinc-500 block">Total Tasks</span>
                      <span className="text-lg font-bold text-zinc-100">
                        {selectedProject.stats?.total_tasks || 0}
                      </span>
                    </div>
                    <div className="p-3 bg-zinc-950 rounded-lg border border-zinc-800">
                      <span className="text-xs text-emerald-500 block">Completed</span>
                      <span className="text-lg font-bold text-emerald-400">
                        {selectedProject.stats?.completed_tasks || 0}
                      </span>
                    </div>
                    <div className="p-3 bg-zinc-950 rounded-lg border border-zinc-800">
                      <span className="text-xs text-blue-500 block">In Progress</span>
                      <span className="text-lg font-bold text-blue-400">
                        {selectedProject.stats?.in_progress_tasks || 0}
                      </span>
                    </div>
                    <div className="p-3 bg-zinc-950 rounded-lg border border-zinc-800">
                      <span className="text-xs text-amber-500 block">Blocked</span>
                      <span className="text-lg font-bold text-amber-400">
                        {selectedProject.stats?.blocked_tasks || 0}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Timestamps */}
                <div className="text-xs text-zinc-500 space-y-1 pt-4 border-t border-zinc-800">
                  <div className="flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5" />
                    Created: {new Date(selectedProject.created_at).toLocaleString()}
                  </div>
                  {selectedProject.completed_at && (
                    <div className="flex items-center gap-1.5 text-purple-400">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Completed: {new Date(selectedProject.completed_at).toLocaleString()}
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="pt-6 border-t border-zinc-800 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Link
                    href={`/projects/${selectedProject.id}/board`}
                    className="px-3.5 py-2 bg-primary hover:bg-primary-hover text-white text-xs font-semibold rounded-lg inline-flex items-center gap-1.5 shadow-sm transition"
                  >
                    <Layers className="h-3.5 w-3.5" />
                    Open Board
                  </Link>
                  <button
                    onClick={() => handleDeleteProject(selectedProject.id)}
                    className="px-3 py-2 bg-rose-600/10 hover:bg-rose-600/20 text-rose-400 border border-rose-500/20 text-xs font-medium rounded-lg inline-flex items-center gap-1.5 transition-colors"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Delete
                  </button>
                </div>
                <button
                  onClick={() => setSelectedProject(null)}
                  className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-medium rounded-lg"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Create Project Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in p-4">
            <div className="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
                  <FolderGit2 className="h-5 w-5 text-blue-400" />
                  Create New Project
                </h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="p-1 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form onSubmit={handleCreateProject} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                    Project Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Q3 Market Expansion"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                    Strategic Objective
                  </label>
                  <input
                    type="text"
                    placeholder="Key result or primary outcome to achieve"
                    value={newObjective}
                    onChange={(e) => setNewObjective(e.target.value)}
                    className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                    Description
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Context, scope, and cross-department milestones..."
                    value={newDescription}
                    onChange={(e) => setNewDescription(e.target.value)}
                    className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      Priority
                    </label>
                    <select
                      value={newPriority}
                      onChange={(e) => setNewPriority(e.target.value)}
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      Initial Status
                    </label>
                    <select
                      value={newStatus}
                      onChange={(e) => setNewStatus(e.target.value)}
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      <option value="PLANNED">Planned</option>
                      <option value="ACTIVE">Active</option>
                      <option value="BLOCKED">Blocked</option>
                    </select>
                  </div>
                </div>

                <div className="pt-4 flex justify-end gap-3 border-t border-zinc-800">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm font-medium rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createSubmitting || !newName.trim()}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg inline-flex items-center gap-2"
                  >
                    {createSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                    Create Project
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
