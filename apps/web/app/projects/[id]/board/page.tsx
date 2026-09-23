"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Eye,
  Filter,
  FolderGit2,
  GripVertical,
  HelpCircle,
  Layers,
  ListTodo,
  Loader2,
  Play,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
  User as UserIcon,
  Users,
  X,
} from "lucide-react";
import {
  api,
  Company,
  Project,
  Task,
  Agent,
  Department,
  ProjectBoardResponse,
} from "@/lib/api";
import { ShellLayout } from "@/components/shell/ShellLayout";

// Visual token styling for task statuses and columns
const COLUMN_STYLES: Record<
  string,
  {
    headerBg: string;
    border: string;
    badgeBg: string;
    badgeText: string;
    accentDot: string;
    targetStatus: string;
  }
> = {
  READY: {
    headerBg: "bg-blue-500/10",
    border: "border-blue-500/20",
    badgeBg: "bg-blue-500/20",
    badgeText: "text-blue-300",
    accentDot: "bg-blue-400",
    targetStatus: "READY",
  },
  IN_PROGRESS: {
    headerBg: "bg-amber-500/10",
    border: "border-amber-500/20",
    badgeBg: "bg-amber-500/20",
    badgeText: "text-amber-300",
    accentDot: "bg-amber-400",
    targetStatus: "IN_PROGRESS",
  },
  WAITING: {
    headerBg: "bg-yellow-500/10",
    border: "border-yellow-500/20",
    badgeBg: "bg-yellow-500/20",
    badgeText: "text-yellow-300",
    accentDot: "bg-yellow-400",
    targetStatus: "WAITING",
  },
  BLOCKED: {
    headerBg: "bg-rose-500/10",
    border: "border-rose-500/20",
    badgeBg: "bg-rose-500/20",
    badgeText: "text-rose-300",
    accentDot: "bg-rose-400",
    targetStatus: "BLOCKED",
  },
  VERIFYING: {
    headerBg: "bg-indigo-500/10",
    border: "border-indigo-500/20",
    badgeBg: "bg-indigo-500/20",
    badgeText: "text-indigo-300",
    accentDot: "bg-indigo-400",
    targetStatus: "VERIFYING",
  },
  COMPLETED: {
    headerBg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    badgeBg: "bg-emerald-500/20",
    badgeText: "text-emerald-300",
    accentDot: "bg-emerald-400",
    targetStatus: "COMPLETED",
  },
  ARCHIVED: {
    headerBg: "bg-zinc-500/10",
    border: "border-zinc-500/20",
    badgeBg: "bg-zinc-500/20",
    badgeText: "text-zinc-300",
    accentDot: "bg-zinc-400",
    targetStatus: "CANCELLED",
  },
};

const PRIORITY_BADGES: Record<string, { label: string; text: string; bg: string; border: string }> = {
  critical: {
    label: "Critical",
    text: "text-rose-400 font-semibold",
    bg: "bg-rose-500/15",
    border: "border-rose-500/30",
  },
  high: {
    label: "High",
    text: "text-amber-400 font-medium",
    bg: "bg-amber-500/15",
    border: "border-amber-500/30",
  },
  medium: {
    label: "Medium",
    text: "text-blue-400",
    bg: "bg-blue-500/15",
    border: "border-blue-500/30",
  },
  low: {
    label: "Low",
    text: "text-zinc-400",
    bg: "bg-zinc-500/15",
    border: "border-zinc-500/30",
  },
};

export default function ProjectBoardPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = (params?.id as string) || "";

  const [activeCompany, setActiveCompany] = useState<Company | null>(null);
  const [boardData, setBoardData] = useState<ProjectBoardResponse | null>(null);
  const [allProjects, setAllProjects] = useState<Project[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);

  // Loading & Error States
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [assigneeFilter, setAssigneeFilter] = useState("ALL");
  const [departmentFilter, setDepartmentFilter] = useState("ALL");
  const [onlyBlocked, setOnlyBlocked] = useState(false);
  const [showArchived, setShowArchived] = useState(false);

  // Drag & Drop State
  const [draggingTaskId, setDraggingTaskId] = useState<string | null>(null);
  const [hoverColumnId, setHoverColumnId] = useState<string | null>(null);
  const [updatingTaskId, setUpdatingTaskId] = useState<string | null>(null);

  // Detail Drawer & Task Creation Modal
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showCreateTaskModal, setShowCreateTaskModal] = useState(false);
  const [createSubmitting, setCreateSubmitting] = useState(false);

  // Quick Task Creation Form State
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskObjective, setNewTaskObjective] = useState("");
  const [newTaskDescription, setNewTaskDescription] = useState("");
  const [newTaskPriority, setNewTaskPriority] = useState<"low" | "medium" | "high" | "critical">("medium");
  const [newTaskStatus, setNewTaskStatus] = useState("READY");
  const [newTaskAgentId, setNewTaskAgentId] = useState("");
  const [newTaskDeptId, setNewTaskDeptId] = useState("");
  const [newTaskDeadline, setNewTaskDeadline] = useState("");

  // Load Companies and Board Data
  const loadData = useCallback(
    async (isManualRefresh = false) => {
      if (isManualRefresh) setRefreshing(true);
      setError(null);
      setActionError(null);

      try {
        const comps = await api.getCompanies();
        if (comps.length === 0) {
          setError("No companies found. Please create a company first.");
          setLoading(false);
          setRefreshing(false);
          return;
        }

        const comp = comps[0];
        setActiveCompany(comp);

        // Fetch Board Data for this project
        const board = await api.getProjectBoard(comp.id, projectId);
        setBoardData(board);

        // Fetch companion datasets for filters and dropdowns
        const [projList, agentList, deptList] = await Promise.all([
          api.getProjects(comp.id, { limit: 100 }),
          api.getAgents(comp.id),
          api.getDepartments(comp.id),
        ]);

        setAllProjects(projList.items);
        setAgents(agentList);
        setDepartments(deptList);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load project board");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [projectId]
  );

  useEffect(() => {
    if (projectId) {
      loadData();
    }
  }, [projectId, loadData]);

  // Current Dragging Task Reference
  const draggingTask = useMemo(() => {
    if (!draggingTaskId || !boardData) return null;
    return boardData.tasks.find((t) => t.id === draggingTaskId) || null;
  }, [draggingTaskId, boardData]);

  // Allowed target statuses for current dragging task
  const allowedDropStatuses = useMemo(() => {
    if (!draggingTask || !boardData) return new Set<string>();
    const targets = boardData.allowed_transitions[draggingTask.status] || [];
    return new Set(targets);
  }, [draggingTask, boardData]);

  // Filter Tasks
  const filteredTasks = useMemo(() => {
    if (!boardData) return [];

    return boardData.tasks.filter((task) => {
      // Search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesTitle = task.title.toLowerCase().includes(q);
        const matchesObj = (task.objective || "").toLowerCase().includes(q);
        const matchesDesc = (task.description || "").toLowerCase().includes(q);
        if (!matchesTitle && !matchesObj && !matchesDesc) return false;
      }

      // Priority
      if (priorityFilter !== "ALL" && task.priority.toLowerCase() !== priorityFilter.toLowerCase()) {
        return false;
      }

      // Assignee
      if (assigneeFilter !== "ALL") {
        if (task.assigned_to_agent_id !== assigneeFilter) return false;
      }

      // Department
      if (departmentFilter !== "ALL") {
        if (task.department_id !== departmentFilter) return false;
      }

      // Only Blocked
      if (onlyBlocked && task.status !== "BLOCKED") {
        return false;
      }

      return true;
    });
  }, [boardData, searchQuery, priorityFilter, assigneeFilter, departmentFilter, onlyBlocked]);

  // Group filtered tasks by Column ID
  const tasksByColumn = useMemo(() => {
    const grouped: Record<string, Task[]> = {};
    if (!boardData) return grouped;

    for (const col of boardData.columns) {
      grouped[col.id] = [];
    }

    for (const task of filteredTasks) {
      for (const col of boardData.columns) {
        if (col.statuses.includes(task.status)) {
          if (!grouped[col.id]) grouped[col.id] = [];
          grouped[col.id].push(task);
          break;
        }
      }
    }

    return grouped;
  }, [boardData, filteredTasks]);

  // Drag and Drop Event Handlers
  const handleDragStart = (e: React.DragEvent, task: Task) => {
    e.dataTransfer.setData("text/plain", task.id);
    e.dataTransfer.effectAllowed = "move";
    setDraggingTaskId(task.id);
    setActionError(null);
  };

  const handleDragOver = (e: React.DragEvent, columnId: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    if (hoverColumnId !== columnId) {
      setHoverColumnId(columnId);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = async (e: React.DragEvent, columnId: string) => {
    e.preventDefault();
    setHoverColumnId(null);
    const taskId = e.dataTransfer.getData("text/plain") || draggingTaskId;
    setDraggingTaskId(null);

    if (!taskId || !boardData || !activeCompany) return;

    const task = boardData.tasks.find((t) => t.id === taskId);
    if (!task) return;

    // Check if task is already in this column
    const targetColumn = boardData.columns.find((c) => c.id === columnId);
    if (!targetColumn) return;
    if (targetColumn.statuses.includes(task.status)) {
      return; // Already in this column
    }

    // Determine target status
    const targetStatus = COLUMN_STYLES[columnId]?.targetStatus || targetColumn.statuses[0];

    // Validate against State Machine transitions
    const allowed = boardData.allowed_transitions[task.status] || [];
    if (!allowed.includes(targetStatus)) {
      setActionError(
        `Cannot transition task "${task.title}" from "${task.status}" to "${targetStatus}". Allowed target statuses: [${allowed.join(", ")}].`
      );
      return;
    }

    // Optimistically update local task status
    const previousStatus = task.status;
    setBoardData((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        tasks: prev.tasks.map((t) => (t.id === taskId ? { ...t, status: targetStatus } : t)),
      };
    });

    setUpdatingTaskId(taskId);
    try {
      await api.updateTaskStatus(activeCompany.id, taskId, {
        status: targetStatus,
      });
      // Refresh board data silently in background to keep rollups and timestamps precise
      const freshBoard = await api.getProjectBoard(activeCompany.id, projectId);
      setBoardData(freshBoard);
    } catch (err: unknown) {
      // Rollback optimistic update
      setBoardData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          tasks: prev.tasks.map((t) => (t.id === taskId ? { ...t, status: previousStatus } : t)),
        };
      });
      setActionError(err instanceof Error ? err.message : "Failed to update task status");
    } finally {
      setUpdatingTaskId(null);
    }
  };

  // Status Change from Task Drawer
  const handleDrawerStatusChange = async (newStatus: string) => {
    if (!selectedTask || !activeCompany || !boardData) return;

    setUpdatingTaskId(selectedTask.id);
    setActionError(null);

    try {
      const updated = await api.updateTaskStatus(activeCompany.id, selectedTask.id, {
        status: newStatus,
      });
      setSelectedTask(updated);

      // Refresh board
      const freshBoard = await api.getProjectBoard(activeCompany.id, projectId);
      setBoardData(freshBoard);
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to transition task status");
    } finally {
      setUpdatingTaskId(null);
    }
  };

  // Quick Task Creation Handler
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCompany || !newTaskTitle.trim()) return;

    setCreateSubmitting(true);
    setActionError(null);

    try {
      await api.createTask(activeCompany.id, {
        project_id: projectId,
        title: newTaskTitle.trim(),
        objective: newTaskObjective.trim() || undefined,
        description: newTaskDescription.trim() || undefined,
        priority: newTaskPriority,
        status: newTaskStatus,
        assigned_to_agent_id: newTaskAgentId || undefined,
        department_id: newTaskDeptId || undefined,
        deadline: newTaskDeadline ? new Date(newTaskDeadline).toISOString() : undefined,
      });

      // Reset form and close modal
      setNewTaskTitle("");
      setNewTaskObjective("");
      setNewTaskDescription("");
      setNewTaskPriority("medium");
      setNewTaskStatus("READY");
      setNewTaskAgentId("");
      setNewTaskDeptId("");
      setNewTaskDeadline("");
      setShowCreateTaskModal(false);

      // Reload board
      const freshBoard = await api.getProjectBoard(activeCompany.id, projectId);
      setBoardData(freshBoard);
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to create task");
    } finally {
      setCreateSubmitting(false);
    }
  };

  // Reset Filters
  const resetFilters = () => {
    setSearchQuery("");
    setPriorityFilter("ALL");
    setAssigneeFilter("ALL");
    setDepartmentFilter("ALL");
    setOnlyBlocked(false);
  };

  const hasActiveFilters =
    Boolean(searchQuery.trim()) ||
    priorityFilter !== "ALL" ||
    assigneeFilter !== "ALL" ||
    departmentFilter !== "ALL" ||
    onlyBlocked;

  return (
    <ShellLayout
      pageTitle={boardData?.project?.name ? `${boardData.project.name} — Board` : "Project Board"}
      breadcrumb="Work Management"
    >
      <div className="space-y-6 pb-12">
        {/* Breadcrumbs & Navigation Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 text-xs text-text-muted">
              <Link href="/projects" className="hover:text-text-primary transition-colors flex items-center gap-1">
                <FolderGit2 className="w-3.5 h-3.5 text-primary" />
                Projects
              </Link>
              <span>/</span>
              <span className="text-text-secondary font-medium truncate max-w-xs">
                {boardData?.project.name || "Project"}
              </span>
              <span>/</span>
              <span className="text-primary font-semibold flex items-center gap-1">
                <Layers className="w-3 h-3" />
                Kanban Board
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-bold text-text-primary tracking-tight">
                {boardData?.project.name || "Kanban Board"}
              </h1>

              {boardData?.project && (
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[11px] px-2.5 py-0.5 rounded-full font-medium border ${
                      COLUMN_STYLES[boardData.project.status]?.badgeBg || "bg-surface"
                    } ${COLUMN_STYLES[boardData.project.status]?.badgeText || "text-text-muted"} ${
                      COLUMN_STYLES[boardData.project.status]?.border || "border-border"
                    }`}
                  >
                    {boardData.project.status}
                  </span>
                  <span
                    className={`text-[11px] px-2.5 py-0.5 rounded-full font-medium border uppercase tracking-wider ${
                      PRIORITY_BADGES[boardData.project.priority]?.bg || "bg-surface"
                    } ${PRIORITY_BADGES[boardData.project.priority]?.text || "text-text-muted"} ${
                      PRIORITY_BADGES[boardData.project.priority]?.border || "border-border"
                    }`}
                  >
                    {boardData.project.priority} Priority
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="flex items-center gap-2.5 shrink-0">
            {/* Project Switcher Dropdown */}
            {allProjects.length > 1 && (
              <div className="relative">
                <select
                  value={projectId}
                  onChange={(e) => router.push(`/projects/${e.target.value}/board`)}
                  className="bg-surface border border-border hover:border-text-muted/60 text-xs text-text-secondary rounded-lg px-3 py-2 pr-8 focus:outline-none focus:border-primary transition"
                >
                  {allProjects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <button
              onClick={() => loadData(true)}
              disabled={refreshing}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg bg-surface border border-border hover:bg-surface-elevated text-text-secondary hover:text-text-primary transition disabled:opacity-50"
              title="Refresh Kanban Board"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-primary" : ""}`} />
              <span>Sync</span>
            </button>

            <button
              onClick={() => setShowCreateTaskModal(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-medium rounded-lg bg-primary hover:bg-primary-hover text-white shadow-sm transition"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Task</span>
            </button>
          </div>
        </div>

        {/* Global Action Warning / Error Alert */}
        {actionError && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 flex items-start justify-between gap-3 animate-in fade-in duration-200">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <p className="font-semibold text-rose-200">Workflow State Machine Notice</p>
                <p className="text-rose-300/90 leading-relaxed">{actionError}</p>
              </div>
            </div>
            <button
              onClick={() => setActionError(null)}
              className="p-1 rounded hover:bg-rose-500/20 text-rose-400"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Progress & Summary Metric Banner */}
        {boardData && (
          <div className="p-4 rounded-2xl bg-surface border border-border/80 shadow-sm space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-6 text-xs">
                <div>
                  <span className="text-text-muted">Total Tasks</span>
                  <p className="text-base font-bold text-text-primary">{boardData.summary.total_tasks}</p>
                </div>
                <div className="h-6 w-px bg-border/80" />
                <div>
                  <span className="text-text-muted">In Progress</span>
                  <p className="text-base font-bold text-amber-400">{boardData.summary.in_progress_tasks}</p>
                </div>
                <div className="h-6 w-px bg-border/80" />
                <div>
                  <span className="text-text-muted">Waiting & Approvals</span>
                  <p className="text-base font-bold text-yellow-400">{boardData.summary.waiting_tasks}</p>
                </div>
                <div className="h-6 w-px bg-border/80" />
                <div>
                  <span className="text-text-muted">Blocked</span>
                  <p className="text-base font-bold text-rose-400">{boardData.summary.blocked_tasks}</p>
                </div>
                <div className="h-6 w-px bg-border/80" />
                <div>
                  <span className="text-text-muted">Completed</span>
                  <p className="text-base font-bold text-emerald-400">{boardData.summary.completed_tasks}</p>
                </div>
              </div>

              {/* Completion Rate Pill */}
              <div className="flex items-center gap-3">
                <span className="text-xs text-text-muted">Completion Rate</span>
                <span className="text-xs font-mono font-bold text-primary px-2.5 py-0.5 rounded-full bg-primary/10 border border-primary/20">
                  {boardData.summary.completion_rate}%
                </span>
              </div>
            </div>

            {/* Dynamic Progress Bar */}
            <div className="w-full bg-surface-elevated h-2 rounded-full overflow-hidden border border-border/40">
              <div
                className="bg-gradient-to-r from-primary to-emerald-400 h-full transition-all duration-500 rounded-full"
                style={{ width: `${boardData.summary.completion_rate}%` }}
              />
            </div>
          </div>
        )}

        {/* Filter Controls Bar */}
        <div className="p-3.5 rounded-xl bg-surface border border-border flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-2.5 flex-1 min-w-[320px]">
            {/* Search Input */}
            <div className="relative flex-1 min-w-[180px] max-w-xs">
              <Search className="w-3.5 h-3.5 text-text-muted absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search tasks by title or objective..."
                className="w-full bg-surface-elevated border border-border/80 rounded-lg pl-8 pr-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary transition"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-2.5 top-2.5 text-text-muted hover:text-text-primary"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>

            {/* Priority Filter */}
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-surface-elevated border border-border/80 rounded-lg px-2.5 py-1.5 text-xs text-text-secondary focus:outline-none focus:border-primary transition"
            >
              <option value="ALL">All Priorities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            {/* Assignee Filter */}
            {agents.length > 0 && (
              <select
                value={assigneeFilter}
                onChange={(e) => setAssigneeFilter(e.target.value)}
                className="bg-surface-elevated border border-border/80 rounded-lg px-2.5 py-1.5 text-xs text-text-secondary focus:outline-none focus:border-primary transition max-w-[150px] truncate"
              >
                <option value="ALL">All Assignees</option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name} ({a.role})
                  </option>
                ))}
              </select>
            )}

            {/* Department Filter */}
            {departments.length > 0 && (
              <select
                value={departmentFilter}
                onChange={(e) => setDepartmentFilter(e.target.value)}
                className="bg-surface-elevated border border-border/80 rounded-lg px-2.5 py-1.5 text-xs text-text-secondary focus:outline-none focus:border-primary transition"
              >
                <option value="ALL">All Departments</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            )}

            {/* Only Blocked Toggle */}
            <button
              onClick={() => setOnlyBlocked(!onlyBlocked)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition ${
                onlyBlocked
                  ? "bg-rose-500/15 border-rose-500/30 text-rose-300"
                  : "bg-surface-elevated border-border/80 text-text-muted hover:text-text-secondary"
              }`}
            >
              <AlertTriangle className="w-3 h-3 text-rose-400" />
              <span>Blocked Only</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            {/* Show Archived Toggle */}
            <button
              onClick={() => setShowArchived(!showArchived)}
              className={`text-xs px-2.5 py-1.5 rounded-lg border transition ${
                showArchived
                  ? "bg-primary/10 border-primary/30 text-primary font-medium"
                  : "border-border/60 text-text-muted hover:text-text-secondary"
              }`}
            >
              {showArchived ? "Hide Failed/Cancelled" : "Show Failed/Cancelled"}
            </button>

            {hasActiveFilters && (
              <button
                onClick={resetFilters}
                className="text-xs text-primary hover:text-primary-hover underline font-medium pl-2"
              >
                Reset Filters
              </button>
            )}
          </div>
        </div>

        {/* Loading Spinner */}
        {loading && (
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p className="text-xs text-text-muted">Loading project Kanban board...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="p-6 rounded-2xl bg-surface border border-rose-500/20 text-center space-y-3">
            <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
            <h3 className="text-sm font-semibold text-rose-300">Unable to load Kanban board</h3>
            <p className="text-xs text-text-muted max-w-md mx-auto">{error}</p>
            <button
              onClick={() => loadData(true)}
              className="px-4 py-2 bg-surface-elevated hover:bg-surface border border-border text-xs rounded-lg transition"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Kanban Board Columns View */}
        {!loading && !error && boardData && (
          <div className="overflow-x-auto pb-6">
            <div className="flex items-start gap-4 min-w-[1240px]">
              {boardData.columns
                .filter((col) => col.id !== "ARCHIVED" || showArchived)
                .map((col) => {
                  const style = COLUMN_STYLES[col.id] || COLUMN_STYLES.READY;
                  const columnTasks = tasksByColumn[col.id] || [];

                  // Validate if currently dragged task can be dropped here
                  const isValidDropTarget =
                    draggingTask &&
                    !col.statuses.includes(draggingTask.status) &&
                    allowedDropStatuses.has(style.targetStatus);

                  const isHovered = hoverColumnId === col.id;

                  return (
                    <div
                      key={col.id}
                      onDragOver={(e) => handleDragOver(e, col.id)}
                      onDragLeave={handleDragLeave}
                      onDrop={(e) => handleDrop(e, col.id)}
                      className={`w-80 shrink-0 rounded-2xl bg-surface-card border transition-all duration-200 flex flex-col max-h-[82vh] ${
                        isHovered && isValidDropTarget
                          ? "border-primary ring-2 ring-primary/20 bg-primary/5"
                          : isHovered && !isValidDropTarget
                          ? "border-rose-500/50 bg-rose-500/5 cursor-not-allowed"
                          : isValidDropTarget
                          ? "border-primary/40 bg-surface/80"
                          : "border-border/80"
                      }`}
                    >
                      {/* Column Header */}
                      <div className={`p-3.5 border-b border-border/80 rounded-t-2xl ${style.headerBg} flex items-center justify-between`}>
                        <div className="flex items-center gap-2">
                          <span className={`w-2.5 h-2.5 rounded-full ${style.accentDot}`} />
                          <h3 className="text-xs font-bold text-text-primary tracking-wide">
                            {col.title}
                          </h3>
                        </div>
                        <span className={`text-[11px] font-mono px-2 py-0.5 rounded-full border ${style.badgeBg} ${style.badgeText} ${style.border} font-semibold`}>
                          {columnTasks.length}
                        </span>
                      </div>

                      {/* Column Task Drop Zone */}
                      <div className="p-3 overflow-y-auto space-y-3 flex-1 min-h-[160px]">
                        {columnTasks.length === 0 ? (
                          <div className={`py-10 text-center border-2 border-dashed rounded-xl ${isHovered && isValidDropTarget ? "border-primary/60 bg-primary/10" : "border-border/40 text-text-muted/60"} text-[11px]`}>
                            {isValidDropTarget ? (
                              <span className="text-primary font-medium">Drop task to transition</span>
                            ) : (
                              <span>No tasks in {col.title.toLowerCase()}</span>
                            )}
                          </div>
                        ) : (
                          columnTasks.map((task) => {
                            const isBeingDragged = draggingTaskId === task.id;
                            const isUpdating = updatingTaskId === task.id;
                            const priorityInfo = PRIORITY_BADGES[task.priority] || PRIORITY_BADGES.medium;
                            const isOverdue = task.deadline && new Date(task.deadline) < new Date() && task.status !== "COMPLETED";

                            return (
                              <div
                                key={task.id}
                                draggable
                                onDragStart={(e) => handleDragStart(e, task)}
                                onClick={() => setSelectedTask(task)}
                                className={`group p-3.5 rounded-xl bg-surface border border-border/90 hover:border-primary/60 shadow-sm cursor-grab active:cursor-grabbing transition-all space-y-2.5 relative ${
                                  isBeingDragged ? "opacity-40 scale-95 border-dashed border-primary" : ""
                                } ${isUpdating ? "animate-pulse" : ""}`}
                              >
                                {isUpdating && (
                                  <div className="absolute inset-0 bg-surface/80 rounded-xl flex items-center justify-center z-10">
                                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                                  </div>
                                )}

                                {/* Card Header: Drag grip & Priority */}
                                <div className="flex items-center justify-between gap-2">
                                  <div className="flex items-center gap-1.5 text-text-muted group-hover:text-text-secondary">
                                    <GripVertical className="w-3.5 h-3.5" />
                                    <span className="font-mono text-[10px] text-text-muted">
                                      #{task.id.slice(0, 6)}
                                    </span>
                                  </div>

                                  <span className={`text-[10px] uppercase font-semibold px-2 py-0.5 rounded border ${priorityInfo.bg} ${priorityInfo.text} ${priorityInfo.border}`}>
                                    {priorityInfo.label}
                                  </span>
                                </div>

                                {/* Task Title */}
                                <h4 className="text-xs font-semibold text-text-primary group-hover:text-primary transition-colors line-clamp-2">
                                  {task.title}
                                </h4>

                                {/* Objective or Description snippet */}
                                {task.objective && (
                                  <p className="text-[11px] text-text-muted line-clamp-2 leading-relaxed">
                                    {task.objective}
                                  </p>
                                )}

                                {/* Meta details: Department, Assignee, Deadline */}
                                <div className="pt-2 border-t border-border/60 flex items-center justify-between text-[10px] text-text-muted">
                                  <div className="flex items-center gap-1.5">
                                    {task.assigned_agent_name ? (
                                      <span className="inline-flex items-center gap-1 text-text-secondary font-medium bg-surface-elevated px-1.5 py-0.5 rounded border border-border/60">
                                        <Users className="w-3 h-3 text-primary" />
                                        <span className="truncate max-w-[90px]">{task.assigned_agent_name}</span>
                                      </span>
                                    ) : task.assigned_to_user_id ? (
                                      <span className="inline-flex items-center gap-1 text-text-secondary font-medium bg-surface-elevated px-1.5 py-0.5 rounded border border-border/60">
                                        <UserIcon className="w-3 h-3 text-emerald-400" />
                                        <span>Operator</span>
                                      </span>
                                    ) : (
                                      <span className="text-text-muted italic">Unassigned</span>
                                    )}
                                  </div>

                                  {task.deadline && (
                                    <span
                                      className={`inline-flex items-center gap-1 font-mono ${
                                        isOverdue ? "text-rose-400 font-semibold" : "text-text-muted"
                                      }`}
                                      title={new Date(task.deadline).toLocaleString()}
                                    >
                                      <Clock className="w-3 h-3" />
                                      {new Date(task.deadline).toLocaleDateString(undefined, {
                                        month: "short",
                                        day: "numeric",
                                      })}
                                    </span>
                                  )}
                                </div>

                                {/* Subtasks and Dependencies Pills */}
                                {(task.subtasks_count > 0 || (task.dependencies && task.dependencies.length > 0)) && (
                                  <div className="flex items-center gap-2 pt-1 text-[10px] text-text-muted">
                                    {task.subtasks_count > 0 && (
                                      <span className="inline-flex items-center gap-1 bg-surface-elevated px-1.5 py-0.2 rounded border border-border/60">
                                        <ListTodo className="w-3 h-3 text-text-muted" />
                                        <span>{task.subtasks_count} subtasks</span>
                                      </span>
                                    )}
                                    {task.dependencies && task.dependencies.length > 0 && (
                                      <span className="inline-flex items-center gap-1 bg-surface-elevated px-1.5 py-0.2 rounded border border-border/60">
                                        <ArrowRight className="w-3 h-3 text-text-muted" />
                                        <span>{task.dependencies.length} deps</span>
                                      </span>
                                    )}
                                  </div>
                                )}
                              </div>
                            );
                          })
                        )}
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {/* Task Detail Slide-Over Drawer */}
        {selectedTask && (
          <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex justify-end animate-in fade-in duration-200">
            <div className="w-full max-w-lg bg-surface border-l border-border h-full p-6 overflow-y-auto space-y-6 shadow-2xl flex flex-col justify-between">
              <div className="space-y-5">
                {/* Drawer Header */}
                <div className="flex items-start justify-between gap-3 border-b border-border pb-4">
                  <div className="space-y-1">
                    <span className="font-mono text-xs text-text-muted">
                      Task ID: {selectedTask.id}
                    </span>
                    <h2 className="text-lg font-bold text-text-primary leading-snug">
                      {selectedTask.title}
                    </h2>
                  </div>
                  <button
                    onClick={() => setSelectedTask(null)}
                    className="p-1 rounded-lg hover:bg-surface-elevated text-text-muted hover:text-text-primary"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {/* State Machine Transition Selector */}
                {boardData && (
                  <div className="p-3.5 rounded-xl bg-surface-elevated border border-border space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-text-primary">Status State Machine</span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                          COLUMN_STYLES[selectedTask.status]?.badgeBg || "bg-surface"
                        } ${COLUMN_STYLES[selectedTask.status]?.badgeText || "text-text-muted"}`}
                      >
                        Current: {selectedTask.status}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      <span className="text-[11px] text-text-muted">Advance to:</span>
                      {(boardData.allowed_transitions[selectedTask.status] || []).map((target) => (
                        <button
                          key={target}
                          onClick={() => handleDrawerStatusChange(target)}
                          disabled={updatingTaskId === selectedTask.id}
                          className="px-2.5 py-1 text-[11px] font-medium rounded-lg bg-surface hover:bg-primary/20 hover:text-primary border border-border transition disabled:opacity-50"
                        >
                          {target}
                        </button>
                      ))}
                      {(boardData.allowed_transitions[selectedTask.status] || []).length === 0 && (
                        <span className="text-[11px] text-text-muted italic">
                          Terminal status (no outward transitions)
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Task Objective */}
                {selectedTask.objective && (
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
                      Strategic Objective
                    </h4>
                    <p className="text-xs text-text-primary bg-surface-elevated p-3 rounded-xl border border-border/80 leading-relaxed">
                      {selectedTask.objective}
                    </p>
                  </div>
                )}

                {/* Task Description */}
                {selectedTask.description && (
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
                      Detailed Instructions
                    </h4>
                    <p className="text-xs text-text-secondary leading-relaxed bg-surface-elevated p-3 rounded-xl border border-border/80 whitespace-pre-wrap">
                      {selectedTask.description}
                    </p>
                  </div>
                )}

                {/* Task Deliverable Output */}
                {selectedTask.output && (
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Deliverable & Output
                    </h4>
                    <pre className="text-xs font-mono text-emerald-300 bg-emerald-500/10 p-3 rounded-xl border border-emerald-500/20 whitespace-pre-wrap leading-relaxed">
                      {selectedTask.output}
                    </pre>
                  </div>
                )}

                {/* Error Details */}
                {selectedTask.error_details && (
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-semibold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                      <AlertCircle className="w-3.5 h-3.5" />
                      Failure / Blocker Diagnostics
                    </h4>
                    <pre className="text-xs font-mono text-rose-300 bg-rose-500/10 p-3 rounded-xl border border-rose-500/20 whitespace-pre-wrap leading-relaxed">
                      {selectedTask.error_details}
                    </pre>
                  </div>
                )}

                {/* Attributes Grid */}
                <div className="grid grid-cols-2 gap-3 pt-2 text-xs">
                  <div className="p-3 rounded-xl bg-surface-elevated border border-border/80 space-y-1">
                    <span className="text-text-muted">Assigned Entity</span>
                    <p className="font-semibold text-text-primary truncate">
                      {selectedTask.assigned_agent_name
                        ? `${selectedTask.assigned_agent_name} (${selectedTask.assigned_agent_role || "Agent"})`
                        : selectedTask.assigned_to_user_id
                        ? "Human Operator"
                        : "Unassigned"}
                    </p>
                  </div>

                  <div className="p-3 rounded-xl bg-surface-elevated border border-border/80 space-y-1">
                    <span className="text-text-muted">Department</span>
                    <p className="font-semibold text-text-primary truncate">
                      {selectedTask.department_name || "General Org"}
                    </p>
                  </div>

                  <div className="p-3 rounded-xl bg-surface-elevated border border-border/80 space-y-1">
                    <span className="text-text-muted">Priority Tier</span>
                    <p className="font-semibold capitalize text-text-primary">
                      {selectedTask.priority}
                    </p>
                  </div>

                  <div className="p-3 rounded-xl bg-surface-elevated border border-border/80 space-y-1">
                    <span className="text-text-muted">Target Deadline</span>
                    <p className="font-semibold text-text-primary">
                      {selectedTask.deadline ? new Date(selectedTask.deadline).toLocaleString() : "None specified"}
                    </p>
                  </div>
                </div>

                {/* Dependencies List */}
                {selectedTask.dependencies && selectedTask.dependencies.length > 0 && (
                  <div className="space-y-2 pt-2">
                    <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
                      Prerequisite Dependencies ({selectedTask.dependencies.length})
                    </h4>
                    <div className="space-y-1.5">
                      {selectedTask.dependencies.map((dep) => (
                        <div
                          key={dep.id}
                          className="p-2.5 rounded-lg bg-surface-elevated border border-border/80 text-xs flex items-center justify-between"
                        >
                          <span className="text-text-primary font-medium">
                            {dep.depends_on_task_title || dep.depends_on_task_id}
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface border border-border text-text-muted">
                            {dep.depends_on_task_status || "PENDING"}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Drawer Footer Actions */}
              <div className="pt-4 border-t border-border flex items-center justify-between">
                <Link
                  href="/tasks"
                  className="text-xs text-primary hover:text-primary-hover font-medium flex items-center gap-1"
                >
                  <Eye className="w-3.5 h-3.5" />
                  View in Tasks Table
                </Link>

                <button
                  onClick={() => setSelectedTask(null)}
                  className="px-4 py-2 bg-surface-elevated hover:bg-surface border border-border text-xs rounded-lg transition"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Quick Task Creation Modal */}
        {showCreateTaskModal && (
          <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
            <div className="w-full max-w-lg bg-surface border border-border rounded-2xl p-6 shadow-2xl space-y-5">
              <div className="flex items-center justify-between border-b border-border pb-3.5">
                <div className="flex items-center gap-2">
                  <Plus className="w-4 h-4 text-primary" />
                  <h3 className="text-sm font-bold text-text-primary">
                    Create New Task in {boardData?.project.name}
                  </h3>
                </div>
                <button
                  onClick={() => setShowCreateTaskModal(false)}
                  className="p-1 rounded-lg hover:bg-surface-elevated text-text-muted hover:text-text-primary"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleCreateTask} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Task Title <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={newTaskTitle}
                    onChange={(e) => setNewTaskTitle(e.target.value)}
                    placeholder="e.g. Conduct market evaluation for European expansion"
                    className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary transition"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-text-secondary mb-1">
                      Priority Level
                    </label>
                    <select
                      value={newTaskPriority}
                      onChange={(e) => setNewTaskPriority(e.target.value as any)}
                      className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-xs text-text-secondary focus:outline-none focus:border-primary transition"
                    >
                      <option value="low">Low Priority</option>
                      <option value="medium">Medium Priority</option>
                      <option value="high">High Priority</option>
                      <option value="critical">Critical Priority</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-text-secondary mb-1">
                      Initial Status
                    </label>
                    <select
                      value={newTaskStatus}
                      onChange={(e) => setNewTaskStatus(e.target.value)}
                      className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-xs text-text-secondary focus:outline-none focus:border-primary transition"
                    >
                      <option value="READY">Ready</option>
                      <option value="PLANNED">Planned</option>
                      <option value="CREATED">Created</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-text-secondary mb-1">
                      Assign to Agent
                    </label>
                    <select
                      value={newTaskAgentId}
                      onChange={(e) => setNewTaskAgentId(e.target.value)}
                      className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-xs text-text-secondary focus:outline-none focus:border-primary transition"
                    >
                      <option value="">Unassigned</option>
                      {agents.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.name} ({a.role})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-text-secondary mb-1">
                      Department
                    </label>
                    <select
                      value={newTaskDeptId}
                      onChange={(e) => setNewTaskDeptId(e.target.value)}
                      className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-xs text-text-secondary focus:outline-none focus:border-primary transition"
                    >
                      <option value="">No Department</option>
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Strategic Objective
                  </label>
                  <input
                    type="text"
                    value={newTaskObjective}
                    onChange={(e) => setNewTaskObjective(e.target.value)}
                    placeholder="Clear desired milestone outcome"
                    className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Target Deadline
                  </label>
                  <input
                    type="datetime-local"
                    value={newTaskDeadline}
                    onChange={(e) => setNewTaskDeadline(e.target.value)}
                    className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-xs text-text-primary focus:outline-none focus:border-primary transition"
                  />
                </div>

                <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setShowCreateTaskModal(false)}
                    className="px-4 py-2 bg-surface-elevated hover:bg-surface border border-border text-xs rounded-lg transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createSubmitting}
                    className="px-4 py-2 bg-primary hover:bg-primary-hover text-white text-xs font-semibold rounded-lg shadow-sm transition disabled:opacity-50 flex items-center gap-1.5"
                  >
                    {createSubmitting ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Creating...</span>
                      </>
                    ) : (
                      <>
                        <Plus className="w-3.5 h-3.5" />
                        <span>Create Task</span>
                      </>
                    )}
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
