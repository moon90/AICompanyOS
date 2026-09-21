"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Bot,
  Calendar,
  CheckCircle2,
  CheckSquare,
  Clock,
  ExternalLink,
  GitBranch,
  Layers,
  Link as LinkIcon,
  Loader2,
  Plus,
  Search,
  SlidersHorizontal,
  Trash2,
  User as UserIcon,
  X,
} from "lucide-react";
import Link from "next/link";
import {
  api,
  Agent,
  Company,
  Department,
  Project,
  Task,
  TaskDependency,
} from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string; border: string }> = {
  CREATED: { label: "Created", bg: "bg-zinc-500/10", text: "text-zinc-400", border: "border-zinc-500/20" },
  PLANNED: { label: "Planned", bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/20" },
  READY: { label: "Ready", bg: "bg-cyan-500/10", text: "text-cyan-400", border: "border-cyan-500/20" },
  ASSIGNED: { label: "Assigned", bg: "bg-indigo-500/10", text: "text-indigo-400", border: "border-indigo-500/20" },
  IN_PROGRESS: { label: "In Progress", bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/20" },
  WAITING: { label: "Waiting", bg: "bg-orange-500/10", text: "text-orange-400", border: "border-orange-500/20" },
  BLOCKED: { label: "Blocked", bg: "bg-rose-500/10", text: "text-rose-400", border: "border-rose-500/20" },
  VERIFYING: { label: "Verifying", bg: "bg-yellow-500/10", text: "text-yellow-400", border: "border-yellow-500/20" },
  COMPLETED: { label: "Completed", bg: "bg-purple-500/10", text: "text-purple-400", border: "border-purple-500/20" },
  FAILED: { label: "Failed", bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/20" },
  CANCELLED: { label: "Cancelled", bg: "bg-zinc-600/10", text: "text-zinc-500", border: "border-zinc-600/20" },
  APPROVAL_REQUIRED: { label: "Approval Required", bg: "bg-pink-500/10", text: "text-pink-400", border: "border-pink-500/20" },
};

const TIMELINE_STEPS = ["CREATED", "PLANNED", "ASSIGNED", "IN_PROGRESS", "VERIFYING", "COMPLETED"];

export default function TasksPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [activeCompany, setActiveCompany] = useState<Company | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [totalTasks, setTotalTasks] = useState(0);

  // References for filtering & creation
  const [projects, setProjects] = useState<Project[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [priorityFilter, setPriorityFilter] = useState<string>("ALL");
  const [projectFilter, setProjectFilter] = useState<string>("ALL");
  const [departmentFilter, setDepartmentFilter] = useState<string>("ALL");
  const [agentFilter, setAgentFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Loading & State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals & Detail
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [depTaskIdToAdd, setDepTaskIdToAdd] = useState("");

  // Create Form State
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newObjective, setNewObjective] = useState("");
  const [newProjectId, setNewProjectId] = useState("");
  const [newDepartmentId, setNewDepartmentId] = useState("");
  const [newAgentId, setNewAgentId] = useState("");
  const [newPriority, setNewPriority] = useState("medium");
  const [newStatus, setNewStatus] = useState("CREATED");
  const [newDeadline, setNewDeadline] = useState("");

  // Status update modal state
  const [statusOutputText, setStatusOutputText] = useState("");
  const [statusErrorText, setStatusErrorText] = useState("");

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
      }
    }
    loadCompanies();
  }, []);

  // Load Metadata (Projects, Departments, Agents)
  useEffect(() => {
    if (!activeCompany) return;
    async function loadMeta() {
      try {
        const [projRes, deptRes, agentRes] = await Promise.all([
          api.getProjects(activeCompany!.id),
          api.getDepartments(activeCompany!.id),
          api.getAgents(activeCompany!.id),
        ]);
        setProjects(projRes.items);
        setDepartments(deptRes);
        setAgents(agentRes);
      } catch {
        // Fall back gracefully
      }
    }
    loadMeta();
  }, [activeCompany]);

  // Load Tasks
  const loadTasks = useCallback(async () => {
    if (!activeCompany) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.getTasks(activeCompany.id, {
        project_id: projectFilter !== "ALL" ? projectFilter : undefined,
        status: statusFilter !== "ALL" ? statusFilter : undefined,
        priority: priorityFilter !== "ALL" ? priorityFilter : undefined,
        department_id: departmentFilter !== "ALL" ? departmentFilter : undefined,
        assigned_to_agent_id: agentFilter !== "ALL" ? agentFilter : undefined,
        search: searchQuery.trim() || undefined,
      });
      setTasks(res.items);
      setTotalTasks(res.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load tasks");
    } finally {
      setLoading(false);
    }
  }, [activeCompany, projectFilter, statusFilter, priorityFilter, departmentFilter, agentFilter, searchQuery]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  // Handle Create Task
  async function handleCreateTask(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompany || !newTitle.trim()) return;

    setCreateSubmitting(true);
    try {
      await api.createTask(activeCompany.id, {
        title: newTitle.trim(),
        description: newDescription.trim() || undefined,
        objective: newObjective.trim() || undefined,
        project_id: newProjectId || undefined,
        department_id: newDepartmentId || undefined,
        assigned_to_agent_id: newAgentId || undefined,
        priority: newPriority,
        status: newStatus,
        deadline: newDeadline ? new Date(newDeadline).toISOString() : undefined,
      });
      setShowCreateModal(false);
      setNewTitle("");
      setNewDescription("");
      setNewObjective("");
      setNewProjectId("");
      setNewDepartmentId("");
      setNewAgentId("");
      setNewPriority("medium");
      setNewStatus("CREATED");
      setNewDeadline("");
      await loadTasks();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create task");
    } finally {
      setCreateSubmitting(false);
    }
  }

  // Handle Status Update
  async function handleStatusUpdate(taskId: string, nextStatus: string) {
    if (!activeCompany) return;
    try {
      const updated = await api.updateTaskStatus(activeCompany.id, taskId, {
        status: nextStatus,
        output: statusOutputText.trim() || undefined,
        error_details: statusErrorText.trim() || undefined,
      });
      setSelectedTask(updated);
      setStatusOutputText("");
      setStatusErrorText("");
      await loadTasks();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to transition status");
    }
  }

  // Handle Add Dependency
  async function handleAddDependency(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompany || !selectedTask || !depTaskIdToAdd) return;
    try {
      await api.addTaskDependency(activeCompany.id, selectedTask.id, {
        depends_on_task_id: depTaskIdToAdd,
      });
      const reloaded = await api.getTask(activeCompany.id, selectedTask.id);
      setSelectedTask(reloaded);
      setDepTaskIdToAdd("");
      await loadTasks();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add dependency");
    }
  }

  // Handle Remove Dependency
  async function handleRemoveDependency(dependsOnTaskId: string) {
    if (!activeCompany || !selectedTask) return;
    try {
      await api.removeTaskDependency(activeCompany.id, selectedTask.id, dependsOnTaskId);
      const reloaded = await api.getTask(activeCompany.id, selectedTask.id);
      setSelectedTask(reloaded);
      await loadTasks();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to remove dependency");
    }
  }

  // Handle Delete Task
  async function handleDeleteTask(taskId: string) {
    if (!activeCompany || !confirm("Are you sure you want to delete this task?")) return;
    try {
      await api.deleteTask(activeCompany.id, taskId);
      if (selectedTask?.id === taskId) {
        setSelectedTask(null);
      }
      await loadTasks();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete task");
    }
  }

  return (
    <ShellLayout pageTitle="Tasks" breadcrumb="Work Management">
      <div className="space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-zinc-900/50 p-4 rounded-xl border border-zinc-800">
          <div>
            <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
              <CheckSquare className="h-6 w-6 text-indigo-400" />
              Task Execution Console
            </h1>
            <p className="text-sm text-zinc-400 mt-1">
              Authoritative, verifiable units of work with state machines, specialist agent assignments, and dependency chains.
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
                className="bg-zinc-800 border border-zinc-700 text-zinc-200 text-sm rounded-lg px-3 py-2"
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
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors shadow-sm"
            >
              <Plus className="h-4 w-4" />
              New Task
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

        {/* Multi-faceted Filter Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
          {/* Search */}
          <div className="lg:col-span-2 relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
            <input
              type="text"
              placeholder="Search tasks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-zinc-900/60 border border-zinc-800 rounded-lg text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full py-2 px-3 bg-zinc-900/60 border border-zinc-800 rounded-lg text-sm text-zinc-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Statuses</option>
              {Object.keys(STATUS_CONFIG).map((st) => (
                <option key={st} value={st}>
                  {STATUS_CONFIG[st].label}
                </option>
              ))}
            </select>
          </div>

          {/* Project Filter */}
          <div>
            <select
              value={projectFilter}
              onChange={(e) => setProjectFilter(e.target.value)}
              className="w-full py-2 px-3 bg-zinc-900/60 border border-zinc-800 rounded-lg text-sm text-zinc-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Projects</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Department Filter */}
          <div>
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="w-full py-2 px-3 bg-zinc-900/60 border border-zinc-800 rounded-lg text-sm text-zinc-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          {/* Agent Filter */}
          <div>
            <select
              value={agentFilter}
              onChange={(e) => setAgentFilter(e.target.value)}
              className="w-full py-2 px-3 bg-zinc-900/60 border border-zinc-800 rounded-lg text-sm text-zinc-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Agents</option>
              {agents.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.role})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Tasks Table / Card View */}
        {loading ? (
          <div className="py-16 flex flex-col items-center justify-center text-zinc-500 gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
            <span className="text-sm">Loading task registry...</span>
          </div>
        ) : tasks.length === 0 ? (
          <div className="py-16 text-center bg-zinc-900/30 border border-zinc-800/80 rounded-2xl p-8">
            <CheckSquare className="h-12 w-12 text-zinc-600 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-zinc-300">No tasks found</h3>
            <p className="text-sm text-zinc-500 mt-1 max-w-sm mx-auto">
              Create atomic tasks, link them to projects, and assign specialist agents from the registry.
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg inline-flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Create First Task
            </button>
          </div>
        ) : (
          <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-zinc-300">
                <thead className="bg-zinc-900/80 text-zinc-400 text-xs uppercase tracking-wider border-b border-zinc-800">
                  <tr>
                    <th className="py-3 px-4">Task</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Priority</th>
                    <th className="py-3 px-4">Project</th>
                    <th className="py-3 px-4">Assigned Specialist</th>
                    <th className="py-3 px-4">Prerequisites</th>
                    <th className="py-3 px-4 text-right">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/60">
                  {tasks.map((task) => {
                    const statusCfg = STATUS_CONFIG[task.status] || STATUS_CONFIG.CREATED;
                    const isOverdue = task.deadline && new Date(task.deadline) < new Date() && task.status !== "COMPLETED";

                    return (
                      <tr
                        key={task.id}
                        onClick={() => setSelectedTask(task)}
                        className="hover:bg-zinc-800/40 cursor-pointer transition-colors"
                      >
                        {/* Title & Identifier */}
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2.5">
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">
                              TASK-{task.id.slice(0, 6).toUpperCase()}
                            </span>
                            <span className="font-medium text-zinc-100 hover:text-indigo-400 transition-colors">
                              {task.title}
                            </span>
                          </div>
                          {task.objective && (
                            <p className="text-xs text-zinc-500 mt-1 line-clamp-1 ml-16">
                              {task.objective}
                            </p>
                          )}
                        </td>

                        {/* Status */}
                        <td className="py-3.5 px-4">
                          <span
                            className={`text-xs px-2.5 py-0.5 rounded-full font-medium border ${statusCfg.bg} ${statusCfg.text} ${statusCfg.border}`}
                          >
                            {statusCfg.label}
                          </span>
                        </td>

                        {/* Priority */}
                        <td className="py-3.5 px-4 capitalize text-xs font-medium">
                          <span
                            className={
                              task.priority === "critical"
                                ? "text-rose-400 font-bold"
                                : task.priority === "high"
                                ? "text-amber-400"
                                : task.priority === "medium"
                                ? "text-blue-400"
                                : "text-zinc-400"
                            }
                          >
                            {task.priority}
                          </span>
                        </td>

                        {/* Project */}
                        <td className="py-3.5 px-4 text-xs text-zinc-400">
                          {task.project_name || "—"}
                        </td>

                        {/* Assigned Agent */}
                        <td className="py-3.5 px-4">
                          {task.assigned_agent_name ? (
                            <div className="flex items-center gap-2">
                              <Bot className="h-4 w-4 text-indigo-400" />
                              <div>
                                <span className="text-xs font-medium text-zinc-200 block">
                                  {task.assigned_agent_name}
                                </span>
                                <span className="text-[10px] text-zinc-500 block">
                                  {task.assigned_agent_role}
                                </span>
                              </div>
                            </div>
                          ) : (
                            <span className="text-xs text-zinc-600 italic">Unassigned</span>
                          )}
                        </td>

                        {/* Prerequisites / Dependencies */}
                        <td className="py-3.5 px-4">
                          {task.dependencies && task.dependencies.length > 0 ? (
                            <span className="inline-flex items-center gap-1 text-xs text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded">
                              <GitBranch className="h-3 w-3 text-zinc-500" />
                              {task.dependencies.length} deps
                            </span>
                          ) : (
                            <span className="text-xs text-zinc-600">None</span>
                          )}
                        </td>

                        {/* Created Date */}
                        <td className="py-3.5 px-4 text-right text-xs text-zinc-500">
                          {new Date(task.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Task Detail Drawer (Adheres to docs/UI.md Sections 31 & 32) */}
        {selectedTask && (
          <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-in fade-in">
            <div className="w-full max-w-xl bg-zinc-900 border-l border-zinc-800 h-full overflow-y-auto p-6 flex flex-col justify-between shadow-2xl">
              <div className="space-y-6">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-400">
                        TASK-{selectedTask.id.slice(0, 6).toUpperCase()}
                      </span>
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-medium border ${
                          (STATUS_CONFIG[selectedTask.status] || STATUS_CONFIG.CREATED).bg
                        } ${(STATUS_CONFIG[selectedTask.status] || STATUS_CONFIG.CREATED).text} ${
                          (STATUS_CONFIG[selectedTask.status] || STATUS_CONFIG.CREATED).border
                        }`}
                      >
                        {selectedTask.status}
                      </span>
                      <span className="text-xs text-zinc-400 capitalize">
                        Priority: {selectedTask.priority}
                      </span>
                    </div>
                    <h2 className="text-xl font-bold text-zinc-100">{selectedTask.title}</h2>
                  </div>
                  <button
                    onClick={() => setSelectedTask(null)}
                    className="p-1 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                {/* Status Progression Timeline (docs/UI.md Section 32) */}
                <div className="p-4 bg-zinc-950 rounded-xl border border-zinc-800">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-3 flex items-center gap-2">
                    <Clock className="h-4 w-4 text-indigo-400" />
                    Lifecycle State Timeline
                  </h4>
                  <div className="flex items-center justify-between relative">
                    <div className="absolute left-0 top-3.5 w-full h-0.5 bg-zinc-800 -z-0" />
                    {TIMELINE_STEPS.map((step, idx) => {
                      const isPast =
                        TIMELINE_STEPS.indexOf(selectedTask.status) >= idx ||
                        selectedTask.status === "COMPLETED";
                      const isCurrent = selectedTask.status === step;
                      return (
                        <div key={step} className="flex flex-col items-center z-10">
                          <div
                            className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                              isCurrent
                                ? "bg-indigo-600 text-white ring-4 ring-indigo-500/20"
                                : isPast
                                ? "bg-emerald-500 text-white"
                                : "bg-zinc-800 text-zinc-500"
                            }`}
                          >
                            {isPast && !isCurrent ? (
                              <CheckCircle2 className="h-4 w-4" />
                            ) : (
                              idx + 1
                            )}
                          </div>
                          <span
                            className={`text-[10px] mt-1.5 font-medium ${
                              isCurrent
                                ? "text-indigo-400 font-bold"
                                : isPast
                                ? "text-zinc-300"
                                : "text-zinc-600"
                            }`}
                          >
                            {step}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Status Transition Action Bar */}
                <div className="p-4 bg-zinc-800/40 rounded-xl border border-zinc-800 space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
                    Advance Execution Status
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {["READY", "IN_PROGRESS", "VERIFYING", "COMPLETED", "BLOCKED", "WAITING", "CANCELLED"].map(
                      (st) => (
                        <button
                          key={st}
                          onClick={() => handleStatusUpdate(selectedTask.id, st)}
                          className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-all ${
                            selectedTask.status === st
                              ? "bg-indigo-600 border-indigo-500 text-white font-bold"
                              : "bg-zinc-900 border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                          }`}
                        >
                          {st}
                        </button>
                      )
                    )}
                  </div>
                  <div className="pt-2">
                    <input
                      type="text"
                      placeholder="Optional output or verification note..."
                      value={statusOutputText}
                      onChange={(e) => setStatusOutputText(e.target.value)}
                      className="w-full px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                {/* Assigned Specialist Agent */}
                <div className="space-y-1.5">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
                    Assigned Agent & Department
                  </h4>
                  <div className="p-3 bg-zinc-950 rounded-lg border border-zinc-800 flex items-center justify-between">
                    {selectedTask.assigned_agent_name ? (
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                          <Bot className="h-5 w-5" />
                        </div>
                        <div>
                          <span className="text-sm font-semibold text-zinc-200 block">
                            {selectedTask.assigned_agent_name}
                          </span>
                          <span className="text-xs text-zinc-500 block">
                            {selectedTask.assigned_agent_role} · {selectedTask.department_name || "General"}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <span className="text-xs text-zinc-500 italic">No specialist assigned</span>
                    )}
                    <Link
                      href="/agents"
                      className="text-xs text-indigo-400 hover:text-indigo-300 inline-flex items-center gap-1"
                    >
                      Registry <ExternalLink className="h-3 w-3" />
                    </Link>
                  </div>
                </div>

                {/* Objective & Description */}
                {selectedTask.objective && (
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
                      Objective
                    </h4>
                    <p className="text-sm text-zinc-200 bg-zinc-950 p-3 rounded-lg border border-zinc-800">
                      {selectedTask.objective}
                    </p>
                  </div>
                )}

                {selectedTask.description && (
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
                      Description
                    </h4>
                    <p className="text-sm text-zinc-300 leading-relaxed bg-zinc-950/40 p-3 rounded-lg border border-zinc-800/80">
                      {selectedTask.description}
                    </p>
                  </div>
                )}

                {/* Prerequisites & Dependencies */}
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                    <GitBranch className="h-4 w-4 text-indigo-400" />
                    Prerequisites / Dependencies
                  </h4>

                  {selectedTask.dependencies && selectedTask.dependencies.length > 0 ? (
                    <div className="space-y-2">
                      {selectedTask.dependencies.map((dep) => (
                        <div
                          key={dep.id}
                          className="flex items-center justify-between p-2.5 bg-zinc-950 rounded-lg border border-zinc-800 text-xs"
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-zinc-500">
                              TASK-{dep.depends_on_task_id.slice(0, 6).toUpperCase()}
                            </span>
                            <span className="text-zinc-200 font-medium">
                              {dep.depends_on_task_title || "Prerequisite Task"}
                            </span>
                          </div>
                          <button
                            onClick={() => handleRemoveDependency(dep.depends_on_task_id)}
                            className="text-zinc-500 hover:text-rose-400 transition-colors p-1"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-zinc-500 italic">No prerequisite dependencies.</p>
                  )}

                  {/* Add Dependency Form */}
                  <form onSubmit={handleAddDependency} className="flex gap-2 pt-1">
                    <select
                      value={depTaskIdToAdd}
                      onChange={(e) => setDepTaskIdToAdd(e.target.value)}
                      className="flex-1 px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="">Select prerequisite task...</option>
                      {tasks
                        .filter((t) => t.id !== selectedTask.id)
                        .map((t) => (
                          <option key={t.id} value={t.id}>
                            {t.title} ({t.status})
                          </option>
                        ))}
                    </select>
                    <button
                      type="submit"
                      disabled={!depTaskIdToAdd}
                      className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 text-xs font-medium text-zinc-200 rounded"
                    >
                      Add Dep
                    </button>
                  </form>
                </div>

                {/* Output & Errors */}
                {selectedTask.output && (
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
                      Execution Output / Deliverable
                    </h4>
                    <pre className="text-xs text-zinc-300 bg-zinc-950 p-3 rounded-lg border border-emerald-500/20 font-mono overflow-x-auto whitespace-pre-wrap">
                      {selectedTask.output}
                    </pre>
                  </div>
                )}

                {selectedTask.error_details && (
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-rose-400">
                      Failure Reason / Error Log
                    </h4>
                    <pre className="text-xs text-rose-300 bg-rose-950/20 p-3 rounded-lg border border-rose-500/20 font-mono overflow-x-auto whitespace-pre-wrap">
                      {selectedTask.error_details}
                    </pre>
                  </div>
                )}
              </div>

              {/* Drawer Footer Actions */}
              <div className="pt-6 border-t border-zinc-800 flex justify-between gap-3">
                <button
                  onClick={() => handleDeleteTask(selectedTask.id)}
                  className="px-4 py-2 bg-rose-600/10 hover:bg-rose-600/20 text-rose-400 border border-rose-500/20 text-sm font-medium rounded-lg inline-flex items-center gap-2"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete Task
                </button>
                <button
                  onClick={() => setSelectedTask(null)}
                  className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm font-medium rounded-lg"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Create Task Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in p-4">
            <div className="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
                  <CheckSquare className="h-5 w-5 text-indigo-400" />
                  Create New Task
                </h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="p-1 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form onSubmit={handleCreateTask} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                    Task Title *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Implement user authentication middleware"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                    Objective
                  </label>
                  <input
                    type="text"
                    placeholder="Verifiable expected result or test outcome"
                    value={newObjective}
                    onChange={(e) => setNewObjective(e.target.value)}
                    className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                    Description
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Execution details, specifications, and edge cases..."
                    value={newDescription}
                    onChange={(e) => setNewDescription(e.target.value)}
                    className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      Project
                    </label>
                    <select
                      value={newProjectId}
                      onChange={(e) => setNewProjectId(e.target.value)}
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="">None (Company Task)</option>
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      Assign Specialist
                    </label>
                    <select
                      value={newAgentId}
                      onChange={(e) => setNewAgentId(e.target.value)}
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="">Unassigned</option>
                      {agents.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.name} ({a.role})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      Priority
                    </label>
                    <select
                      value={newPriority}
                      onChange={(e) => setNewPriority(e.target.value)}
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
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
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="CREATED">Created</option>
                      <option value="PLANNED">Planned</option>
                      <option value="READY">Ready</option>
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
                    disabled={createSubmitting || !newTitle.trim()}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg inline-flex items-center gap-2"
                  >
                    {createSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                    Create Task
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
