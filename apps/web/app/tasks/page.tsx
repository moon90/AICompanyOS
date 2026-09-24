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
  Network,
  Play,
  Zap,
  ChevronDown,
  ChevronRight,
  Cpu,
  FileCode,
  LayoutGrid,
  Code2,
  GitCommit,
  GitPullRequest,
  FileDiff,
  Check,
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
  DelegationRecord,
  ExecutionRecord,
  TaskExecuteRequest,
  EngineeringTaskView,
  TaskEngineeringContext,
  TaskFileChange,
  TestStatus,
  VerificationState,
  FileChangeType,
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

  // Phase 7 Task Delegation State
  const [taskDelegations, setTaskDelegations] = useState<DelegationRecord[]>([]);
  const [delegationsLoading, setDelegationsLoading] = useState(false);
  const [showDelegateForm, setShowDelegateForm] = useState(false);
  const [delegateTargetAgentId, setDelegateTargetAgentId] = useState("");
  const [delegateReason, setDelegateReason] = useState("");
  const [delegateSubmitting, setDelegateSubmitting] = useState(false);

  // Phase 8 Agent Runtime Execution State
  const [taskExecutions, setTaskExecutions] = useState<ExecutionRecord[]>([]);
  const [executionsLoading, setExecutionsLoading] = useState(false);
  const [executingTaskId, setExecutingTaskId] = useState<string | null>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);
  const [expandedExecutionId, setExpandedExecutionId] = useState<string | null>(null);
  const [maxStepsInput, setMaxStepsInput] = useState<number>(5);
  const [maxDurationInput, setMaxDurationInput] = useState<number>(60);

  // Engineering File Tracking (Phase 16)
  const [engineeringView, setEngineeringView] = useState<EngineeringTaskView | null>(null);
  const [loadingEngineering, setLoadingEngineering] = useState(false);
  const [showRecordFileModal, setShowRecordFileModal] = useState(false);
  const [showEditContextModal, setShowEditContextModal] = useState(false);
  const [recordingFile, setRecordingFile] = useState(false);
  const [updatingContext, setUpdatingContext] = useState(false);
  const [expandedFileId, setExpandedFileId] = useState<string | null>(null);

  // Record File Form State
  const [rfFilePath, setRfFilePath] = useState("");
  const [rfBranch, setRfBranch] = useState("");
  const [rfRepo, setRfRepo] = useState("");
  const [rfChangeType, setRfChangeType] = useState<FileChangeType>("MODIFIED");
  const [rfCommitHash, setRfCommitHash] = useState("");
  const [rfCommitMsg, setRfCommitMsg] = useState("");
  const [rfAdditions, setRfAdditions] = useState<number>(10);
  const [rfDeletions, setRfDeletions] = useState<number>(2);
  const [rfSummary, setRfSummary] = useState("");

  // Edit Context Form State
  const [ecBranch, setEcBranch] = useState("");
  const [ecRepo, setEcRepo] = useState("");
  const [ecPrNum, setEcPrNum] = useState("");
  const [ecPrUrl, setEcPrUrl] = useState("");
  const [ecPrTitle, setEcPrTitle] = useState("");
  const [ecTestStatus, setEcTestStatus] = useState<TestStatus>("PENDING");
  const [ecTestSummary, setEcTestSummary] = useState("");
  const [ecVerification, setEcVerification] = useState<VerificationState>("PENDING");
  const [ecVerificationNotes, setEcVerificationNotes] = useState("");

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

  // Load Task Delegation Lineage
  const loadTaskDelegations = useCallback(
    async (taskId: string) => {
      if (!activeCompany) return;
      setDelegationsLoading(true);
      try {
        const records = await api.getTaskDelegations(activeCompany.id, taskId);
        setTaskDelegations(records);
      } catch {
        setTaskDelegations([]);
      } finally {
        setDelegationsLoading(false);
      }
    },
    [activeCompany]
  );

  // Load Agent Execution Runs (Phase 8)
  const loadTaskExecutions = useCallback(
    async (taskId: string) => {
      if (!activeCompany) return;
      setExecutionsLoading(true);
      try {
        const res = await api.getTaskExecutions(activeCompany.id, taskId);
        setTaskExecutions(res.items);
        if (res.items.length > 0) {
          setExpandedExecutionId((prev) => prev || res.items[0].id);
        }
      } catch {
        setTaskExecutions([]);
      } finally {
        setExecutionsLoading(false);
      }
    },
    [activeCompany]
  );

  const loadEngineeringView = useCallback(
    async (taskId: string) => {
      if (!activeCompany) return;
      setLoadingEngineering(true);
      try {
        const view = await api.getTaskEngineeringView(activeCompany.id, taskId);
        setEngineeringView(view);
        if (view.context) {
          setEcBranch(view.context.branch);
          setEcRepo(view.context.repository);
          setEcPrNum(view.context.pull_request_number || "");
          setEcPrUrl(view.context.pull_request_url || "");
          setEcPrTitle(view.context.pull_request_title || "");
          setEcTestStatus(view.context.test_status as TestStatus);
          setEcTestSummary(view.context.test_output_summary || "");
          setEcVerification(view.context.verification_state as VerificationState);
          setEcVerificationNotes(view.context.verification_notes || "");
          setRfBranch(view.context.branch);
          setRfRepo(view.context.repository);
        } else {
          setRfBranch("main");
          setRfRepo("main");
          setEcBranch("main");
          setEcRepo("main");
        }
      } catch (err) {
        console.error("Failed to load engineering view:", err);
      } finally {
        setLoadingEngineering(false);
      }
    },
    [activeCompany]
  );

  useEffect(() => {
    if (selectedTask) {
      loadTaskDelegations(selectedTask.id);
      loadTaskExecutions(selectedTask.id);
      loadEngineeringView(selectedTask.id);
    } else {
      setTaskDelegations([]);
      setTaskExecutions([]);
      setExpandedExecutionId(null);
      setExecutionError(null);
      setShowDelegateForm(false);
      setDelegateTargetAgentId("");
      setDelegateReason("");
      setEngineeringView(null);
      setShowRecordFileModal(false);
      setShowEditContextModal(false);
    }
  }, [selectedTask, loadTaskDelegations, loadTaskExecutions, loadEngineeringView]);

  async function handleRecordFileChange(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompany || !selectedTask || !rfFilePath.trim()) return;
    setRecordingFile(true);
    try {
      await api.recordTaskFileChanges(activeCompany.id, selectedTask.id, [
        {
          file_path: rfFilePath.trim(),
          repository: rfRepo.trim() || "main",
          branch: rfBranch.trim() || "main",
          change_type: rfChangeType,
          commit_hash: rfCommitHash.trim() || undefined,
          commit_message: rfCommitMsg.trim() || undefined,
          additions: Number(rfAdditions) || 0,
          deletions: Number(rfDeletions) || 0,
          change_summary: rfSummary.trim() || undefined,
        },
      ]);
      await loadEngineeringView(selectedTask.id);
      setRfFilePath("");
      setRfCommitHash("");
      setRfCommitMsg("");
      setRfSummary("");
      setShowRecordFileModal(false);
    } catch (err: unknown) {
      console.error("Failed to record file change:", err);
    } finally {
      setRecordingFile(false);
    }
  }

  async function handleUpdateEngineeringContext(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompany || !selectedTask) return;
    setUpdatingContext(true);
    try {
      await api.upsertEngineeringContext(activeCompany.id, selectedTask.id, {
        branch: ecBranch.trim() || undefined,
        repository: ecRepo.trim() || undefined,
        pull_request_number: ecPrNum.trim() || undefined,
        pull_request_url: ecPrUrl.trim() || undefined,
        pull_request_title: ecPrTitle.trim() || undefined,
        test_status: ecTestStatus,
        test_output_summary: ecTestSummary.trim() || undefined,
        verification_state: ecVerification,
        verification_notes: ecVerificationNotes.trim() || undefined,
      });
      await loadEngineeringView(selectedTask.id);
      setShowEditContextModal(false);
    } catch (err: unknown) {
      console.error("Failed to update context:", err);
    } finally {
      setUpdatingContext(false);
    }
  }

  async function handleQuickVerify(state: VerificationState) {
    if (!activeCompany || !selectedTask) return;
    try {
      await api.upsertEngineeringContext(activeCompany.id, selectedTask.id, {
        verification_state: state,
        verification_notes:
          state === "VERIFIED"
            ? "Code review passed and verified by operator."
            : "Verification rejected. Revision requested.",
      });
      await loadEngineeringView(selectedTask.id);
    } catch (err: unknown) {
      console.error("Failed to update verification state:", err);
    }
  }

  // Handle Agent Runtime Execution (Phase 8)
  async function handleExecuteTask(taskId: string, customLimits?: TaskExecuteRequest) {
    if (!activeCompany) return;
    setExecutingTaskId(taskId);
    setExecutionError(null);
    try {
      const limits: TaskExecuteRequest = customLimits || {
        max_steps: maxStepsInput || 5,
        max_duration_seconds: maxDurationInput || 60,
      };
      await api.executeTask(activeCompany.id, taskId, limits);
      const reloaded = await api.getTask(activeCompany.id, taskId);
      setSelectedTask(reloaded);
      await loadTaskExecutions(taskId);
      await loadTasks();
    } catch (err: unknown) {
      setExecutionError(err instanceof Error ? err.message : "Agent execution failed");
    } finally {
      setExecutingTaskId(null);
    }
  }

  // Handle Operator Verification & Completion (Phase 8 Golden Rule)
  async function handleVerifyAndComplete(taskId: string) {
    if (!activeCompany) return;
    try {
      const updated = await api.updateTaskStatus(activeCompany.id, taskId, {
        status: "COMPLETED",
        output: selectedTask?.output || "Deliverable verified and accepted by operator.",
      });
      setSelectedTask(updated);
      await loadTasks();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to verify and complete task");
    }
  }

  // Handle Deterministic Task Delegation (Phase 7)
  async function handleDelegateTask(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompany || !selectedTask || !delegateTargetAgentId) return;

    setDelegateSubmitting(true);
    setError(null);
    try {
      await api.delegateTask(activeCompany.id, selectedTask.id, {
        target_agent_id: delegateTargetAgentId,
        reason: delegateReason.trim() || undefined,
      });
      const reloaded = await api.getTask(activeCompany.id, selectedTask.id);
      setSelectedTask(reloaded);
      await loadTaskDelegations(selectedTask.id);
      await loadTasks();
      setShowDelegateForm(false);
      setDelegateTargetAgentId("");
      setDelegateReason("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delegate task");
    } finally {
      setDelegateSubmitting(false);
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
            {projects.length > 0 && (
              <Link
                href={`/projects/${projectFilter !== "ALL" ? projectFilter : projects[0].id}/board`}
                className="inline-flex items-center gap-2 px-3.5 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-sm font-medium rounded-lg border border-zinc-700 transition-colors shadow-sm"
                title="Open interactive Kanban board for project"
              >
                <LayoutGrid className="h-4 w-4 text-emerald-400" />
                <span>Kanban Board</span>
              </Link>
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
                    <th className="py-3 px-4">Created</th>
                    <th className="py-3 px-4 text-right">Action</th>
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
                        <td className="py-3.5 px-4 text-xs text-zinc-500">
                          {new Date(task.created_at).toLocaleDateString()}
                        </td>

                        {/* Quick Actions (Phase 8 Execution & Verification) */}
                        <td className="py-3.5 px-4 text-right">
                          {task.status === "VERIFYING" ? (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedTask(task);
                              }}
                              className="px-2.5 py-1 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-300 border border-yellow-500/30 text-xs font-semibold rounded inline-flex items-center gap-1.5 transition-all"
                            >
                              <CheckCircle2 className="h-3 w-3 text-yellow-400" />
                              Verify
                            </button>
                          ) : task.assigned_to_agent_id && ["ASSIGNED", "READY", "FAILED"].includes(task.status) ? (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleExecuteTask(task.id);
                              }}
                              disabled={executingTaskId === task.id}
                              className="px-2.5 py-1 bg-indigo-600/20 hover:bg-indigo-600/30 disabled:opacity-50 text-indigo-300 border border-indigo-500/30 text-xs font-medium rounded inline-flex items-center gap-1.5 transition-all"
                            >
                              {executingTaskId === task.id ? (
                                <Loader2 className="h-3 w-3 animate-spin text-indigo-400" />
                              ) : (
                                <Zap className="h-3 w-3 text-indigo-400" />
                              )}
                              Run
                            </button>
                          ) : (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedTask(task);
                              }}
                              className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
                            >
                              Details →
                            </button>
                          )}
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

                {/* Phase 8 Verification Banner (Golden Rule: Agent completion advances to VERIFYING, operator review required) */}
                {selectedTask.status === "VERIFYING" && (
                  <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-xl space-y-3 animate-in fade-in">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="flex items-center gap-2.5">
                        <Clock className="h-5 w-5 text-yellow-400 animate-pulse shrink-0" />
                        <div>
                          <span className="text-xs font-bold text-yellow-300 uppercase tracking-wider block">
                            Phase 8 Verification Guard
                          </span>
                          <span className="text-xs text-yellow-200/80 block">
                            Agent completed execution. Review the output deliverable below and confirm completion.
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleVerifyAndComplete(selectedTask.id)}
                        className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg shadow-sm inline-flex items-center gap-2 shrink-0 transition-colors"
                      >
                        <CheckCircle2 className="h-4 w-4" />
                        Verify & Complete Task
                      </button>
                    </div>
                  </div>
                )}

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
                {/* Assigned Specialist Agent & Phase 7 Delegation Trigger */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
                      Assigned Agent & Department
                    </h4>
                    <button
                      onClick={() => setShowDelegateForm(!showDelegateForm)}
                      className="text-xs text-indigo-400 hover:text-indigo-300 inline-flex items-center gap-1 font-medium transition-colors"
                    >
                      <Network className="h-3.5 w-3.5" />
                      {showDelegateForm ? "Cancel Delegation" : "Delegate Task"}
                    </button>
                  </div>
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

                  {/* Inline Delegation Control Panel (Phase 7) */}
                  {showDelegateForm && (
                    <form
                      onSubmit={handleDelegateTask}
                      className="p-3.5 bg-zinc-950/90 rounded-lg border border-indigo-500/30 space-y-3 animate-in fade-in"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-indigo-300 flex items-center gap-1.5">
                          <Network className="h-3.5 w-3.5" />
                          Hierarchical Delegation
                        </span>
                        <span className="text-[10px] text-zinc-500 font-mono">Max Depth: 3</span>
                      </div>
                      <div>
                        <label className="text-[11px] text-zinc-400 block mb-1">Target Agent *</label>
                        <select
                          required
                          value={delegateTargetAgentId}
                          onChange={(e) => setDelegateTargetAgentId(e.target.value)}
                          className="w-full px-2.5 py-1.5 bg-zinc-900 border border-zinc-700 rounded text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        >
                          <option value="">Select recipient specialist agent...</option>
                          {agents
                            .filter((a) => a.id !== selectedTask.assigned_to_agent_id)
                            .map((a) => (
                              <option key={a.id} value={a.id}>
                                {a.name} ({a.role} · {a.department?.name || "General"})
                              </option>
                            ))}
                        </select>
                      </div>
                      <div>
                        <label className="text-[11px] text-zinc-400 block mb-1">Delegation Directive / Reason</label>
                        <input
                          type="text"
                          placeholder="e.g. Assigning domain implementation to technical specialist"
                          value={delegateReason}
                          onChange={(e) => setDelegateReason(e.target.value)}
                          className="w-full px-2.5 py-1.5 bg-zinc-900 border border-zinc-700 rounded text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        />
                      </div>
                      <div className="flex justify-end gap-2 pt-1">
                        <button
                          type="button"
                          onClick={() => setShowDelegateForm(false)}
                          className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300 rounded"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={delegateSubmitting || !delegateTargetAgentId}
                          className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-xs text-white font-medium rounded inline-flex items-center gap-1.5"
                        >
                          {delegateSubmitting && <Loader2 className="h-3 w-3 animate-spin" />}
                          Confirm Delegation
                        </button>
                      </div>
                    </form>
                  )}
                </div>

                {/* Delegation Lineage Audit Trail (Phase 7) */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                      <Network className="h-4 w-4 text-indigo-400" />
                      Delegation Lineage ({taskDelegations.length})
                    </h4>
                    {taskDelegations.length > 0 && (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">
                        Max Depth: {Math.max(...taskDelegations.map((d) => d.depth))}
                      </span>
                    )}
                  </div>

                  {delegationsLoading ? (
                    <div className="p-3 bg-zinc-950 rounded-lg border border-zinc-800 flex items-center justify-center text-xs text-zinc-500 gap-2">
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-400" />
                      Loading lineage...
                    </div>
                  ) : taskDelegations.length === 0 ? (
                    <div className="p-3 bg-zinc-950/60 rounded-lg border border-zinc-800 text-xs text-zinc-500 italic">
                      No delegation hops recorded. Direct assignment or unassigned.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {taskDelegations.map((rec, idx) => (
                        <div
                          key={rec.id}
                          className="p-3 bg-zinc-950 rounded-lg border border-zinc-800 space-y-1.5 text-xs"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 font-mono text-[10px] font-bold border border-indigo-500/20">
                                Hop {idx + 1} (Depth {rec.depth})
                              </span>
                              <span className="font-medium text-zinc-200">
                                {rec.delegated_by_agent_name ||
                                  rec.delegated_by_user_name ||
                                  (rec.delegated_by_user_id ? "Human Operator" : "System / CEO")}
                              </span>
                              <ArrowRight className="h-3 w-3 text-zinc-500" />
                              <span className="font-medium text-indigo-300">
                                {rec.delegated_to_agent_name || "Specialist Agent"}
                              </span>
                            </div>
                            <span className="text-[10px] text-zinc-500 font-mono">
                              {new Date(rec.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                            </span>
                          </div>
                          {rec.reason && (
                            <p className="text-zinc-400 text-[11px] bg-zinc-900/60 p-2 rounded border border-zinc-800/80">
                              <span className="text-zinc-500 font-medium">Directive:</span> {rec.reason}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Phase 8 Agent Runtime Execution Engine */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                      <Cpu className="h-4 w-4 text-indigo-400" />
                      Agent Runtime Engine (Execution Bounds)
                    </h4>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                      Phase 8 Active
                    </span>
                  </div>

                  {selectedTask.assigned_to_agent_id ? (
                    <div className="p-4 bg-zinc-950 rounded-xl border border-zinc-800 space-y-3.5">
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-xs font-semibold text-zinc-200 block">
                            Run Specialist Agent: {selectedTask.assigned_agent_name}
                          </span>
                          <span className="text-[11px] text-zinc-500">
                            Bounded reasoning loop with automatic deliverable capture & verification guard
                          </span>
                        </div>
                        <button
                          onClick={() => handleExecuteTask(selectedTask.id)}
                          disabled={
                            executingTaskId === selectedTask.id ||
                            !["ASSIGNED", "READY", "PLANNED", "FAILED"].includes(selectedTask.status)
                          }
                          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-xs font-semibold text-white rounded-lg inline-flex items-center gap-2 shadow-sm transition-all"
                        >
                          {executingTaskId === selectedTask.id ? (
                            <>
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                              Running Agent...
                            </>
                          ) : (
                            <>
                              <Zap className="h-3.5 w-3.5 text-indigo-200" />
                              Execute Agent
                            </>
                          )}
                        </button>
                      </div>

                      <div className="grid grid-cols-2 gap-3 pt-2 border-t border-zinc-800/80">
                        <div>
                          <label className="text-[11px] text-zinc-400 block mb-1">
                            Max Steps (Budget Limit)
                          </label>
                          <input
                            type="number"
                            min={1}
                            max={20}
                            value={maxStepsInput}
                            onChange={(e) => setMaxStepsInput(Number(e.target.value))}
                            className="w-full px-2.5 py-1.5 bg-zinc-900 border border-zinc-700 rounded text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="text-[11px] text-zinc-400 block mb-1">
                            Timeout Guard (Seconds)
                          </label>
                          <input
                            type="number"
                            min={5}
                            max={300}
                            value={maxDurationInput}
                            onChange={(e) => setMaxDurationInput(Number(e.target.value))}
                            className="w-full px-2.5 py-1.5 bg-zinc-900 border border-zinc-700 rounded text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                          />
                        </div>
                      </div>

                      {executionError && (
                        <div className="p-2.5 bg-rose-950/40 border border-rose-500/30 rounded text-xs text-rose-300 flex items-center gap-2">
                          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                          <span>{executionError}</span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="p-3 bg-zinc-950/60 rounded-lg border border-zinc-800 text-xs text-zinc-500 italic">
                      Assign a specialist agent to this task before running the execution engine.
                    </div>
                  )}
                </div>

                {/* Execution Run History (Phase 8 Audit Trail) */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                      <Cpu className="h-4 w-4 text-indigo-400" />
                      Execution Run History ({taskExecutions.length})
                    </h4>
                    {taskExecutions.length > 0 && (
                      <span className="text-[10px] font-mono text-zinc-400">
                        Latest: {new Date(taskExecutions[0].created_at).toLocaleTimeString()}
                      </span>
                    )}
                  </div>

                  {executionsLoading ? (
                    <div className="p-4 bg-zinc-950 rounded-lg border border-zinc-800 flex items-center justify-center text-xs text-zinc-500 gap-2">
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-400" />
                      Loading execution history...
                    </div>
                  ) : taskExecutions.length === 0 ? (
                    <div className="p-3 bg-zinc-950/60 rounded-lg border border-zinc-800 text-xs text-zinc-500 italic">
                      No execution runs recorded yet. Click &quot;Execute Agent&quot; above to launch bounded reasoning.
                    </div>
                  ) : (
                    <div className="space-y-2.5">
                      {taskExecutions.map((run) => (
                        <div
                          key={run.id}
                          className="p-3.5 bg-zinc-950 rounded-xl border border-zinc-800 space-y-2.5"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span
                                className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                                  run.status === "SUCCESS"
                                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                    : run.status === "FAILED"
                                    ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                                    : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                }`}
                              >
                                {run.status}
                              </span>
                              <span className="text-xs font-medium text-zinc-200">
                                {run.agent_name || "Specialist Agent"}
                              </span>
                              <span className="text-[11px] text-zinc-500 font-mono">
                                ({run.duration_ms}ms · {run.step_count} steps · {run.tokens_used} tokens · $
                                {run.estimated_cost.toFixed(4)})
                              </span>
                            </div>
                            <button
                              onClick={() =>
                                setExpandedExecutionId(
                                  expandedExecutionId === run.id ? null : run.id
                                )
                              }
                              className="text-xs text-zinc-400 hover:text-indigo-400 inline-flex items-center gap-1 font-medium transition-colors"
                            >
                              {expandedExecutionId === run.id ? "Hide Details" : "View Steps & Output"}
                              {expandedExecutionId === run.id ? (
                                <ChevronDown className="h-3.5 w-3.5" />
                              ) : (
                                <ChevronRight className="h-3.5 w-3.5" />
                              )}
                            </button>
                          </div>

                          {run.result_summary && (
                            <p className="text-xs text-zinc-300 bg-zinc-900/60 p-2 rounded border border-zinc-800">
                              {run.result_summary}
                            </p>
                          )}

                          {expandedExecutionId === run.id && (
                            <div className="space-y-3 pt-2 border-t border-zinc-800/80">
                              {/* Step Transcript */}
                              {run.steps_json && run.steps_json.length > 0 && (
                                <div className="space-y-1.5">
                                  <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">
                                    Reasoning Step Transcript ({run.steps_json.length} steps)
                                  </span>
                                  <div className="space-y-2">
                                    {run.steps_json.map((step) => (
                                      <div
                                        key={step.step_number}
                                        className="p-2.5 bg-zinc-900/80 rounded-lg border border-zinc-800 text-xs space-y-1 font-mono"
                                      >
                                        <div className="flex items-center justify-between text-[11px] text-indigo-400 font-bold">
                                          <span>
                                            Step {step.step_number}: {step.action}
                                          </span>
                                          <span className="text-zinc-500 font-normal">
                                            {step.duration_ms}ms · {step.tokens_used} tokens
                                          </span>
                                        </div>
                                        <p className="text-zinc-300 font-sans text-xs">
                                          <span className="text-zinc-500 font-medium">Thought:</span>{" "}
                                          {step.thought}
                                        </p>
                                        {step.observation && (
                                          <p className="text-zinc-400 font-sans text-xs bg-zinc-950 p-1.5 rounded">
                                            <span className="text-zinc-500 font-medium">Observation:</span>{" "}
                                            {step.observation}
                                          </p>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Deliverable preview */}
                              {run.deliverable && (
                                <div className="space-y-1.5">
                                  <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block flex items-center gap-1.5">
                                    <FileCode className="h-3.5 w-3.5" />
                                    Run Deliverable
                                  </span>
                                  <pre className="text-xs text-zinc-300 bg-zinc-950 p-3 rounded-lg border border-emerald-500/20 font-mono overflow-x-auto whitespace-pre-wrap max-h-64">
                                    {run.deliverable}
                                  </pre>
                                </div>
                              )}

                              {run.error_details && (
                                <div className="space-y-1.5">
                                  <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider block">
                                    Execution Error Details
                                  </span>
                                  <pre className="text-xs text-rose-300 bg-rose-950/20 p-2.5 rounded-lg border border-rose-500/20 font-mono overflow-x-auto whitespace-pre-wrap">
                                    {run.error_details}
                                  </pre>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
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

                {/* Engineering & Code Tracking (Phase 16 - docs/Phases.md § 20 & docs/Memory.md § 61) */}
                <div className="p-4 bg-zinc-950/80 rounded-xl border border-zinc-800 space-y-4 shadow-inner">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                        <Code2 className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-200 flex items-center gap-2">
                          Engineering &amp; Code
                          <span className="text-[10px] font-mono font-normal px-1.5 py-0.2 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                            Phase 16
                          </span>
                        </h4>
                        <span className="text-[11px] text-zinc-500">
                          Operational Git context, PR links &amp; changed files
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => setShowRecordFileModal(true)}
                        className="px-2.5 py-1 text-xs bg-cyan-600/10 hover:bg-cyan-600/20 text-cyan-400 border border-cyan-500/20 font-medium rounded-lg inline-flex items-center gap-1 transition-all"
                        title="Record code changes"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Log Change
                      </button>
                      <button
                        onClick={() => setShowEditContextModal(true)}
                        className="px-2.5 py-1 text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-medium rounded-lg inline-flex items-center gap-1 transition-all"
                        title="Configure Git branch, PR, or test state"
                      >
                        <SlidersHorizontal className="h-3.5 w-3.5" />
                        Config
                      </button>
                    </div>
                  </div>

                  {loadingEngineering ? (
                    <div className="py-6 flex items-center justify-center gap-2 text-xs text-zinc-500">
                      <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
                      Loading engineering context...
                    </div>
                  ) : (
                    <>
                      {/* Context Metadata Cards */}
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {/* Branch & Commits */}
                        <div className="p-2.5 bg-zinc-900/60 rounded-lg border border-zinc-800/80 space-y-1">
                          <span className="text-[10px] uppercase font-semibold text-zinc-500 block">
                            Branch &amp; Commits
                          </span>
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-cyan-300 font-medium inline-flex items-center gap-1 truncate max-w-[150px]">
                              <GitBranch className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                              {engineeringView?.context?.branch || "main"}
                            </span>
                            <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700/60">
                              {engineeringView?.context?.commit_count || 0} commits
                            </span>
                          </div>
                        </div>

                        {/* Pull Request */}
                        <div className="p-2.5 bg-zinc-900/60 rounded-lg border border-zinc-800/80 space-y-1">
                          <span className="text-[10px] uppercase font-semibold text-zinc-500 block">
                            Pull Request
                          </span>
                          {engineeringView?.context?.pull_request_number ? (
                            <a
                              href={engineeringView.context.pull_request_url || "#"}
                              target="_blank"
                              rel="noreferrer"
                              className="font-mono text-purple-300 hover:text-purple-200 font-medium inline-flex items-center gap-1 truncate max-w-[170px]"
                            >
                              <GitPullRequest className="h-3.5 w-3.5 text-purple-400 shrink-0" />
                              #{engineeringView.context.pull_request_number}
                              <ExternalLink className="h-3 w-3 opacity-70" />
                            </a>
                          ) : (
                            <span className="text-zinc-500 italic text-[11px]">No PR linked</span>
                          )}
                        </div>

                        {/* Automated Test Status */}
                        <div className="p-2.5 bg-zinc-900/60 rounded-lg border border-zinc-800/80 space-y-1">
                          <span className="text-[10px] uppercase font-semibold text-zinc-500 block">
                            Test Status
                          </span>
                          <div className="flex items-center gap-1.5">
                            {engineeringView?.context?.test_status === "PASSED" ? (
                              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                                Passed
                              </span>
                            ) : engineeringView?.context?.test_status === "FAILED" ? (
                              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-400">
                                <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
                                Failed
                              </span>
                            ) : engineeringView?.context?.test_status === "RUNNING" ? (
                              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-400">
                                <Loader2 className="h-3.5 w-3.5 text-amber-400 animate-spin" />
                                Running
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-[11px] text-zinc-400">
                                <Clock className="h-3.5 w-3.5 text-zinc-500" />
                                {engineeringView?.context?.test_status || "Pending"}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Verification State */}
                        <div className="p-2.5 bg-zinc-900/60 rounded-lg border border-zinc-800/80 space-y-1">
                          <span className="text-[10px] uppercase font-semibold text-zinc-500 block">
                            Verification State
                          </span>
                          <div className="flex items-center justify-between">
                            <span
                              className={`text-[11px] font-semibold inline-flex items-center gap-1 ${
                                engineeringView?.context?.verification_state === "VERIFIED"
                                  ? "text-emerald-400"
                                  : engineeringView?.context?.verification_state === "REJECTED"
                                  ? "text-rose-400"
                                  : engineeringView?.context?.verification_state === "IN_REVIEW"
                                  ? "text-blue-400"
                                  : "text-zinc-400"
                              }`}
                            >
                              {engineeringView?.context?.verification_state === "VERIFIED" && (
                                <Check className="h-3.5 w-3.5 text-emerald-400" />
                              )}
                              {engineeringView?.context?.verification_state || "Pending"}
                            </span>

                            {/* Quick Verify buttons */}
                            <div className="flex items-center gap-1">
                              {engineeringView?.context?.verification_state !== "VERIFIED" && (
                                <button
                                  onClick={() => handleQuickVerify("VERIFIED")}
                                  className="px-1.5 py-0.5 text-[10px] rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 font-medium"
                                  title="Approve and mark verified"
                                >
                                  Verify
                                </button>
                              )}
                              {engineeringView?.context?.verification_state !== "REJECTED" && (
                                <button
                                  onClick={() => handleQuickVerify("REJECTED")}
                                  className="px-1.5 py-0.5 text-[10px] rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 font-medium"
                                  title="Reject code changes"
                                >
                                  Reject
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Changed Files List */}
                      <div className="space-y-2 pt-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-zinc-300 flex items-center gap-1.5">
                            <FileDiff className="h-3.5 w-3.5 text-cyan-400" />
                            Tracked Files ({engineeringView?.total_files_changed || 0})
                          </span>
                          <span className="text-[11px] font-mono">
                            <span className="text-emerald-400 font-medium">
                              +{engineeringView?.total_additions || 0}
                            </span>{" "}
                            /{" "}
                            <span className="text-rose-400 font-medium">
                              -{engineeringView?.total_deletions || 0}
                            </span>
                          </span>
                        </div>

                        {engineeringView?.file_changes && engineeringView.file_changes.length > 0 ? (
                          <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                            {engineeringView.file_changes.map((fc) => {
                              const isExpanded = expandedFileId === fc.id;
                              return (
                                <div
                                  key={fc.id}
                                  onClick={() => setExpandedFileId(isExpanded ? null : fc.id)}
                                  className="p-2.5 bg-zinc-900/70 hover:bg-zinc-900 border border-zinc-800/80 rounded-lg text-xs cursor-pointer transition-colors space-y-1.5"
                                >
                                  <div className="flex items-center justify-between gap-2">
                                    <div className="flex items-center gap-2 min-w-0">
                                      <span
                                        className={`text-[9px] font-mono font-bold uppercase px-1.5 py-0.5 rounded ${
                                          fc.change_type === "ADDED"
                                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                            : fc.change_type === "DELETED"
                                            ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                                            : fc.change_type === "RENAMED"
                                            ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                                            : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                        }`}
                                      >
                                        {fc.change_type}
                                      </span>
                                      <span className="font-mono text-zinc-200 truncate font-medium">
                                        {fc.file_path}
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-2 shrink-0">
                                      <span className="font-mono text-[11px] text-zinc-400">
                                        <span className="text-emerald-400 font-semibold">+{fc.additions}</span>{" "}
                                        <span className="text-rose-400 font-semibold">-{fc.deletions}</span>
                                      </span>
                                      <ChevronRight
                                        className={`h-3.5 w-3.5 text-zinc-500 transition-transform ${
                                          isExpanded ? "rotate-90" : ""
                                        }`}
                                      />
                                    </div>
                                  </div>

                                  {isExpanded && (
                                    <div className="pt-2 border-t border-zinc-800/60 text-[11px] space-y-1 text-zinc-400 font-sans">
                                      <div className="flex items-center justify-between text-zinc-500 font-mono text-[10px]">
                                        <span>Author: {fc.agent_name}</span>
                                        {fc.commit_hash && <span>Commit: {fc.commit_hash.slice(0, 7)}</span>}
                                      </div>
                                      {fc.commit_message && (
                                        <p className="text-zinc-300 font-mono text-[10px]">
                                          &gt; {fc.commit_message}
                                        </p>
                                      )}
                                      {fc.change_summary && (
                                        <p className="text-zinc-400 italic bg-zinc-950/80 p-2 rounded border border-zinc-800/50">
                                          {fc.change_summary}
                                        </p>
                                      )}
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          <div className="py-4 text-center text-xs text-zinc-500 italic bg-zinc-900/30 rounded-lg border border-zinc-800/50">
                            No files logged for this task yet. Click &quot;Log Change&quot; to record code changes.
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>

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

        {/* Record File Change Modal (Phase 16) */}
        {showRecordFileModal && selectedTask && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in p-4">
            <div className="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                <h3 className="text-base font-bold text-zinc-100 flex items-center gap-2">
                  <FileDiff className="h-5 w-5 text-cyan-400" />
                  Log Code File Change
                </h3>
                <button
                  onClick={() => setShowRecordFileModal(false)}
                  className="p-1 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form onSubmit={handleRecordFileChange} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                    File Path *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. apps/web/app/tasks/page.tsx"
                    value={rfFilePath}
                    onChange={(e) => setRfFilePath(e.target.value)}
                    className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs font-mono text-zinc-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      Change Type
                    </label>
                    <select
                      value={rfChangeType}
                      onChange={(e) => setRfChangeType(e.target.value as FileChangeType)}
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                    >
                      <option value="MODIFIED">MODIFIED</option>
                      <option value="ADDED">ADDED</option>
                      <option value="DELETED">DELETED</option>
                      <option value="RENAMED">RENAMED</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      Branch
                    </label>
                    <input
                      type="text"
                      value={rfBranch}
                      onChange={(e) => setRfBranch(e.target.value)}
                      placeholder="main"
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs font-mono text-zinc-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      Lines Added (+)
                    </label>
                    <input
                      type="number"
                      min={0}
                      value={rfAdditions}
                      onChange={(e) => setRfAdditions(parseInt(e.target.value) || 0)}
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-emerald-400 font-mono focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      Lines Deleted (-)
                    </label>
                    <input
                      type="number"
                      min={0}
                      value={rfDeletions}
                      onChange={(e) => setRfDeletions(parseInt(e.target.value) || 0)}
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-rose-400 font-mono focus:outline-none focus:ring-1 focus:ring-rose-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      Commit Hash (Optional)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. 7f8a9b2"
                      value={rfCommitHash}
                      onChange={(e) => setRfCommitHash(e.target.value)}
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs font-mono text-zinc-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      Commit Message (Optional)
                    </label>
                    <input
                      type="text"
                      placeholder="feat: implement tracking drawer"
                      value={rfCommitMsg}
                      onChange={(e) => setRfCommitMsg(e.target.value)}
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                    Diff / Change Summary
                  </label>
                  <textarea
                    rows={2}
                    placeholder="Short description of changes, refactors, or fixes..."
                    value={rfSummary}
                    onChange={(e) => setRfSummary(e.target.value)}
                    className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  />
                </div>

                <div className="pt-3 flex justify-end gap-3 border-t border-zinc-800">
                  <button
                    type="button"
                    onClick={() => setShowRecordFileModal(false)}
                    className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-medium rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={recordingFile || !rfFilePath.trim()}
                    className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg inline-flex items-center gap-2"
                  >
                    {recordingFile && <Loader2 className="h-4 w-4 animate-spin" />}
                    Save File Change
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Edit Engineering Context Modal (Phase 16) */}
        {showEditContextModal && selectedTask && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in p-4">
            <div className="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                <h3 className="text-base font-bold text-zinc-100 flex items-center gap-2">
                  <SlidersHorizontal className="h-5 w-5 text-indigo-400" />
                  Configure Git &amp; Verification Context
                </h3>
                <button
                  onClick={() => setShowEditContextModal(false)}
                  className="p-1 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form onSubmit={handleUpdateEngineeringContext} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      Git Branch
                    </label>
                    <input
                      type="text"
                      value={ecBranch}
                      onChange={(e) => setEcBranch(e.target.value)}
                      placeholder="feat/feature-name"
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs font-mono text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      Repository
                    </label>
                    <input
                      type="text"
                      value={ecRepo}
                      onChange={(e) => setEcRepo(e.target.value)}
                      placeholder="org/repo"
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs font-mono text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      PR Number
                    </label>
                    <input
                      type="text"
                      value={ecPrNum}
                      onChange={(e) => setEcPrNum(e.target.value)}
                      placeholder="e.g. 42"
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      PR URL
                    </label>
                    <input
                      type="url"
                      value={ecPrUrl}
                      onChange={(e) => setEcPrUrl(e.target.value)}
                      placeholder="https://github.com/..."
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      Test Status
                    </label>
                    <select
                      value={ecTestStatus}
                      onChange={(e) => setEcTestStatus(e.target.value as TestStatus)}
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="PENDING">PENDING</option>
                      <option value="RUNNING">RUNNING</option>
                      <option value="PASSED">PASSED</option>
                      <option value="FAILED">FAILED</option>
                      <option value="SKIPPED">SKIPPED</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                      Verification State
                    </label>
                    <select
                      value={ecVerification}
                      onChange={(e) => setEcVerification(e.target.value as VerificationState)}
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="PENDING">PENDING</option>
                      <option value="IN_REVIEW">IN_REVIEW</option>
                      <option value="VERIFIED">VERIFIED</option>
                      <option value="REJECTED">REJECTED</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                    Test Output Summary
                  </label>
                  <textarea
                    rows={2}
                    value={ecTestSummary}
                    onChange={(e) => setEcTestSummary(e.target.value)}
                    placeholder="e.g. 187/187 tests passed, 0 failures, 100% coverage..."
                    className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
                    Verification Notes
                  </label>
                  <textarea
                    rows={2}
                    value={ecVerificationNotes}
                    onChange={(e) => setEcVerificationNotes(e.target.value)}
                    placeholder="e.g. Reviewed architecture diffs and confirmed test evidence..."
                    className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div className="pt-3 flex justify-end gap-3 border-t border-zinc-800">
                  <button
                    type="button"
                    onClick={() => setShowEditContextModal(false)}
                    className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-medium rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={updatingContext}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg inline-flex items-center gap-2"
                  >
                    {updatingContext && <Loader2 className="h-4 w-4 animate-spin" />}
                    Save Context
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
