/**
 * API client for interacting with the AI Company OS backend.
 */

export interface User {
  id: string;
  name: string;
  email: string;
  status: string;
  created_at: string;
  last_login_at: string | null;
}

export interface AuthResponse {
  user: User;
  token: string;
  token_type: string;
}

export interface SystemStatus {
  status: string;
  database: string;
  auth_authority: string;
  environment: string;
  version: string;
  current_phase: string;
  timestamp: string;
}

export interface Company {
  id: string;
  name: string;
  description: string | null;
  mission: string | null;
  industry: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  user_role: string | null;
}

export interface Department {
  id: string;
  company_id: string;
  name: string;
  code: string;
  description: string | null;
  lead_role: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CompanyMember {
  id: string;
  company_id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  role: string;
  status: string;
  created_at: string;
}

export interface AgentDefinition {
  id: string;
  agent_id: string;
  version: string;
  system_prompt: string | null;
  model: string;
  capabilities: string[];
  tools: string[];
  configuration: Record<string, unknown>;
  is_current: boolean;
  created_at: string;
}

export interface Agent {
  id: string;
  company_id: string;
  department_id: string | null;
  department: {
    id: string;
    name: string;
    code: string;
  } | null;
  name: string;
  role: string;
  type: string;
  reports_to: string | null;
  manager: {
    id: string;
    name: string;
    role: string;
  } | null;
  mission: string | null;
  status: string;
  authority_level: string;
  created_at: string;
  updated_at: string;
  current_definition: AgentDefinition | null;
}

export interface CeoContext {
  company: {
    id: string;
    name: string;
    description: string | null;
    mission: string | null;
    industry: string | null;
    status: string;
  };
  ceo_agent: {
    id: string;
    name: string;
    role: string;
    authority_level: string;
    status: string;
  } | null;
  departments: Array<{
    id: string;
    name: string;
    code: string;
    lead_role: string | null;
  }>;
  agents: Array<{
    id: string;
    name: string;
    role: string;
    type: string;
    authority_level: string;
    reports_to: string | null;
    department_id: string | null;
    department_code: string | null;
    department_name: string | null;
    mission: string | null;
    model: string;
    version: string;
    capabilities: string[];
    tools: string[];
  }>;
  agent_count: number;
  department_count: number;
}

export interface PlanStep {
  step_id: string;
  title: string;
  description: string;
  assigned_agent_id: string | null;
  assigned_agent_role: string;
  department_code: string | null;
  depends_on: string[];
  required_capabilities: string[];
  expected_output: string;
  verification_criteria: string;
}

export interface DelegationProposal {
  proposal_id: string;
  source_agent_id: string | null;
  target_agent_id: string | null;
  target_role: string;
  objective: string;
  scope: string;
  expected_output: string;
  required_capabilities: string[];
  constraints: string[];
  authority_level_required: number;
}

export interface ApprovalRequirement {
  step_id: string;
  action_description: string;
  risk_level: "low" | "medium" | "high" | "critical";
  reason_for_approval: string;
}

export interface CeoPlanSummary {
  id: string;
  company_id: string;
  user_id: string;
  ceo_agent_id: string | null;
  goal: string;
  requested_outcome: string | null;
  priority: string;
  status: string;
  reasoning_summary: string;
  step_count: number;
  created_at: string;
  updated_at: string;
}

export interface CeoPlanDetail {
  id: string;
  company_id: string;
  user_id: string;
  ceo_agent_id: string | null;
  goal: string;
  requested_outcome: string | null;
  priority: string;
  status: string;
  reasoning_summary: string;
  context_snapshot: Record<string, unknown>;
  plan_steps: PlanStep[];
  delegation_proposals: DelegationProposal[];
  approval_requirements: ApprovalRequirement[];
  risks: Array<{ risk: string; mitigation: string; severity?: string }>;
  assumptions: string[];
  created_at: string;
  updated_at: string;
}

export interface CreatePlanPayload {
  objective: string;
  requested_outcome?: string;
  constraints?: string[];
  priority?: "low" | "medium" | "high" | "critical";
  requirements?: string[];
}

export interface AgentDetail extends Agent {
  definitions: AgentDefinition[];
  subordinates: Array<{
    id: string;
    name: string;
    role: string;
    status: string;
  }>;
}

export interface ProjectTaskStats {
  total_tasks: number;
  completed_tasks: number;
  blocked_tasks: number;
  in_progress_tasks: number;
  planned_tasks: number;
}

export interface Project {
  id: string;
  company_id: string;
  name: string;
  description: string | null;
  objective: string | null;
  status: string;
  priority: string;
  owner_user_id: string | null;
  owner_agent_id: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  stats?: ProjectTaskStats;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
}

export interface KanbanColumn {
  id: string;
  title: string;
  statuses: string[];
  color: string;
  task_count: number;
}

export interface BoardSummaryStats {
  total_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  waiting_tasks: number;
  blocked_tasks: number;
  completion_rate: number;
}

export interface ProjectBoardResponse {
  project: Project;
  columns: KanbanColumn[];
  tasks: Task[];
  allowed_transitions: Record<string, string[]>;
  summary: BoardSummaryStats;
}

export interface TaskDependency {
  id: string;
  task_id: string;
  depends_on_task_id: string;
  depends_on_task_title: string | null;
  depends_on_task_status: string | null;
  created_at: string;
}

export interface Task {
  id: string;
  company_id: string;
  project_id: string | null;
  parent_task_id: string | null;
  title: string;
  description: string | null;
  objective: string | null;
  created_by_user_id: string | null;
  assigned_to_agent_id: string | null;
  assigned_to_user_id: string | null;
  department_id: string | null;
  status: string;
  priority: string;
  deadline: string | null;
  output: string | null;
  error_details: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  project_name: string | null;
  assigned_agent_name: string | null;
  assigned_agent_role: string | null;
  department_name: string | null;
  dependencies: TaskDependency[];
  subtasks_count: number;
}

export interface TaskListResponse {
  items: Task[];
  total: number;
}

export interface DelegationRecord {
  id: string;
  company_id: string;
  task_id: string;
  delegated_by_user_id: string | null;
  delegated_by_agent_id: string | null;
  delegated_to_agent_id: string;
  scope: string | null;
  reason: string;
  depth: number;
  status: string;
  created_at: string;
  delegated_to_agent_name: string | null;
  delegated_to_agent_role: string | null;
  delegated_by_agent_name: string | null;
  delegated_by_user_name: string | null;
}

export interface ExecutionStep {
  step_number: number;
  thought: string;
  action: string;
  action_input: Record<string, unknown>;
  observation: string;
  duration_ms: number;
  tokens_used: number;
}

export interface ExecutionRecord {
  id: string;
  company_id: string;
  task_id: string;
  agent_id: string;
  executed_by_user_id: string | null;
  status: string;
  step_count: number;
  duration_ms: number;
  tokens_used: number;
  estimated_cost: number;
  result_summary: string | null;
  deliverable: string | null;
  steps_json: ExecutionStep[];
  error_details: string | null;
  created_at: string;
  completed_at: string | null;
  agent_name?: string | null;
  agent_role?: string | null;
}

export interface ExecutionListResponse {
  total: number;
  items: ExecutionRecord[];
}

export interface TaskExecuteRequest {
  max_steps?: number;
  max_duration_seconds?: number;
  max_tokens?: number;
  max_cost?: number;
}

export interface DelegationListResponse {
  items: DelegationRecord[];
  total: number;
}

export interface PlanDelegationResult {
  plan_id: string;
  project_id: string;
  project_name: string;
  parent_task_id: string;
  parent_task_title: string;
  child_tasks_count: number;
  child_task_ids: string[];
  dependencies_count: number;
  delegations_count: number;
}

export interface ToolDefinition {
  name: string;
  provider: string;
  description: string;
  version: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  requires_approval: boolean;
  allowed_roles: string[];
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
}

export interface ToolListResponse {
  items: ToolDefinition[];
  total: number;
}

export interface ToolExecuteRequest {
  agent_id: string;
  tool_name: string;
  action?: string;
  parameters?: Record<string, unknown>;
  task_id?: string;
  execution_id?: string;
}

export interface ToolExecutionRecord {
  id: string;
  company_id: string;
  agent_id: string;
  task_id?: string | null;
  execution_id?: string | null;
  tool_name: string;
  action: string;
  risk_level: string;
  requires_approval: boolean;
  status: "SUCCESS" | "FAILED" | "APPROVAL_REQUIRED" | "BLOCKED" | string;
  input_params: Record<string, unknown>;
  output_data: Record<string, unknown>;
  error_details?: string | null;
  duration_ms: number;
  created_at: string;
}

export interface ToolExecutionListResponse {
  items: ToolExecutionRecord[];
  total: number;
}

export interface ApprovalRequest {
  id: string;
  company_id: string;
  task_id?: string | null;
  agent_id?: string | null;
  execution_id?: string | null;
  tool_execution_id?: string | null;
  action_type: string;
  description: string;
  payload: Record<string, unknown>;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED";
  reviewed_by_user_id?: string | null;
  reviewed_at?: string | null;
  decision_reason?: string | null;
  created_at: string;
  updated_at: string;
  agent_name?: string | null;
  task_title?: string | null;
  reviewer_name?: string | null;
  tool_name?: string | null;
}

export interface ApprovalListResponse {
  items: ApprovalRequest[];
  total: number;
}

export interface ApprovalDecisionRequest {
  decision_reason?: string;
}

export interface ApiError {
  detail: string;
  status: number;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // Ensures cookies (ai_company_session) are sent and received
  });

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errorJson = await response.json();
      if (errorJson && typeof errorJson.detail === "string") {
        errorDetail = errorJson.detail;
      }
    } catch {
      errorDetail = response.statusText || errorDetail;
    }

    const error: ApiError = {
      detail: errorDetail,
      status: response.status,
    };
    throw error;
  }

  return response.json() as Promise<T>;
}

export const api = {
  async register(
    name: string,
    email: string,
    password: string,
    confirmPassword: string
  ): Promise<User> {
    return request<User>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({
        name,
        email,
        password,
        confirm_password: confirmPassword,
      }),
    });
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    return request<AuthResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  async logout(): Promise<{ message: string }> {
    return request<{ message: string }>("/api/v1/auth/logout", {
      method: "POST",
    });
  },

  async getMe(): Promise<User> {
    return request<User>("/api/v1/auth/me", {
      method: "GET",
    });
  },

  async getSystemStatus(): Promise<SystemStatus> {
    return request<SystemStatus>("/api/v1/system/status", {
      method: "GET",
    });
  },

  async getCompanies(): Promise<Company[]> {
    return request<Company[]>("/api/v1/companies", {
      method: "GET",
    });
  },

  async getCompany(companyId: string): Promise<Company> {
    return request<Company>(`/api/v1/companies/${companyId}`, {
      method: "GET",
    });
  },

  async createCompany(data: {
    name: string;
    description?: string;
    mission?: string;
    industry?: string;
  }): Promise<Company> {
    return request<Company>("/api/v1/companies", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateCompany(
    companyId: string,
    data: {
      name?: string;
      description?: string;
      mission?: string;
      industry?: string;
      status?: string;
    }
  ): Promise<Company> {
    return request<Company>(`/api/v1/companies/${companyId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async getDepartments(companyId: string): Promise<Department[]> {
    return request<Department[]>(`/api/v1/companies/${companyId}/departments`, {
      method: "GET",
    });
  },

  async createDepartment(
    companyId: string,
    data: {
      name: string;
      code: string;
      description?: string;
      lead_role?: string;
    }
  ): Promise<Department> {
    return request<Department>(`/api/v1/companies/${companyId}/departments`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateDepartment(
    companyId: string,
    departmentId: string,
    data: {
      name?: string;
      description?: string;
      lead_role?: string;
      status?: string;
    }
  ): Promise<Department> {
    return request<Department>(
      `/api/v1/companies/${companyId}/departments/${departmentId}`,
      {
        method: "PATCH",
        body: JSON.stringify(data),
      }
    );
  },

  async getCompanyMembers(companyId: string): Promise<CompanyMember[]> {
    return request<CompanyMember[]>(`/api/v1/companies/${companyId}/members`, {
      method: "GET",
    });
  },

  async getAgents(
    companyId: string,
    params?: { department_id?: string; status?: string }
  ): Promise<Agent[]> {
    const query = new URLSearchParams();
    if (params?.department_id) query.set("department_id", params.department_id);
    if (params?.status) query.set("status", params.status);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<Agent[]>(`/api/v1/companies/${companyId}/agents${qs}`, {
      method: "GET",
    });
  },

  async getAgent(companyId: string, agentId: string): Promise<AgentDetail> {
    return request<AgentDetail>(
      `/api/v1/companies/${companyId}/agents/${agentId}`,
      {
        method: "GET",
      }
    );
  },

  async createAgent(
    companyId: string,
    data: {
      name: string;
      role: string;
      type?: string;
      department_id?: string | null;
      reports_to?: string | null;
      mission?: string;
      authority_level?: string;
      system_prompt?: string;
      model?: string;
      capabilities?: string[];
      tools?: string[];
      configuration?: Record<string, unknown>;
    }
  ): Promise<Agent> {
    return request<Agent>(`/api/v1/companies/${companyId}/agents`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateAgent(
    companyId: string,
    agentId: string,
    data: {
      name?: string;
      role?: string;
      type?: string;
      department_id?: string | null;
      reports_to?: string | null;
      mission?: string;
      status?: string;
      authority_level?: string;
    }
  ): Promise<Agent> {
    return request<Agent>(
      `/api/v1/companies/${companyId}/agents/${agentId}`,
      {
        method: "PATCH",
        body: JSON.stringify(data),
      }
    );
  },

  async provisionDefaultAgents(companyId: string): Promise<Agent[]> {
    return request<Agent[]>(
      `/api/v1/companies/${companyId}/agents/provision-defaults`,
      {
        method: "POST",
      }
    );
  },

  async createAgentDefinition(
    companyId: string,
    agentId: string,
    data: {
      version: string;
      system_prompt?: string;
      model?: string;
      capabilities?: string[];
      tools?: string[];
      configuration?: Record<string, unknown>;
    }
  ): Promise<AgentDefinition> {
    return request<AgentDefinition>(
      `/api/v1/companies/${companyId}/agents/${agentId}/definitions`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  async getAgentDefinitions(
    companyId: string,
    agentId: string
  ): Promise<AgentDefinition[]> {
    return request<AgentDefinition[]>(
      `/api/v1/companies/${companyId}/agents/${agentId}/definitions`,
      {
        method: "GET",
      }
    );
  },

  async getCeoContext(companyId: string): Promise<CeoContext> {
    return request<CeoContext>(`/api/v1/companies/${companyId}/ceo/context`, {
      method: "GET",
    });
  },

  async createPlan(
    companyId: string,
    payload: CreatePlanPayload
  ): Promise<CeoPlanDetail> {
    return request<CeoPlanDetail>(`/api/v1/companies/${companyId}/ceo/plan`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getPlans(companyId: string): Promise<CeoPlanSummary[]> {
    return request<CeoPlanSummary[]>(`/api/v1/companies/${companyId}/ceo/plans`, {
      method: "GET",
    });
  },

  async getPlan(companyId: string, planId: string): Promise<CeoPlanDetail> {
    return request<CeoPlanDetail>(
      `/api/v1/companies/${companyId}/ceo/plans/${planId}`,
      {
        method: "GET",
      }
    );
  },

  async getProjects(
    companyId: string,
    params?: {
      status?: string;
      priority?: string;
      search?: string;
      limit?: number;
      offset?: number;
    }
  ): Promise<ProjectListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.priority) searchParams.set("priority", params.priority);
    if (params?.search) searchParams.set("search", params.search);
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.offset) searchParams.set("offset", params.offset.toString());
    const qs = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return request<ProjectListResponse>(`/api/v1/companies/${companyId}/projects${qs}`, {
      method: "GET",
    });
  },

  async createProject(
    companyId: string,
    data: {
      name: string;
      description?: string;
      objective?: string;
      status?: string;
      priority?: string;
      owner_user_id?: string;
      owner_agent_id?: string;
    }
  ): Promise<Project> {
    return request<Project>(`/api/v1/companies/${companyId}/projects`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getProject(companyId: string, projectId: string): Promise<Project> {
    return request<Project>(`/api/v1/companies/${companyId}/projects/${projectId}`, {
      method: "GET",
    });
  },

  async getProjectBoard(companyId: string, projectId: string): Promise<ProjectBoardResponse> {
    return request<ProjectBoardResponse>(
      `/api/v1/companies/${companyId}/projects/${projectId}/board`,
      { method: "GET" }
    );
  },

  async updateProject(
    companyId: string,
    projectId: string,
    data: Partial<{
      name: string;
      description: string;
      objective: string;
      status: string;
      priority: string;
      owner_user_id: string;
      owner_agent_id: string;
    }>
  ): Promise<Project> {
    return request<Project>(`/api/v1/companies/${companyId}/projects/${projectId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async deleteProject(companyId: string, projectId: string): Promise<void> {
    return request<void>(`/api/v1/companies/${companyId}/projects/${projectId}`, {
      method: "DELETE",
    });
  },

  async getTasks(
    companyId: string,
    params?: {
      project_id?: string;
      parent_task_id?: string;
      status?: string;
      priority?: string;
      department_id?: string;
      assigned_to_agent_id?: string;
      search?: string;
      limit?: number;
      offset?: number;
    }
  ): Promise<TaskListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.project_id) searchParams.set("project_id", params.project_id);
    if (params?.parent_task_id) searchParams.set("parent_task_id", params.parent_task_id);
    if (params?.status) searchParams.set("status", params.status);
    if (params?.priority) searchParams.set("priority", params.priority);
    if (params?.department_id) searchParams.set("department_id", params.department_id);
    if (params?.assigned_to_agent_id) searchParams.set("assigned_to_agent_id", params.assigned_to_agent_id);
    if (params?.search) searchParams.set("search", params.search);
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.offset) searchParams.set("offset", params.offset.toString());
    const qs = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return request<TaskListResponse>(`/api/v1/companies/${companyId}/tasks${qs}`, {
      method: "GET",
    });
  },

  async createTask(
    companyId: string,
    data: {
      title: string;
      description?: string;
      objective?: string;
      project_id?: string;
      parent_task_id?: string;
      assigned_to_agent_id?: string;
      assigned_to_user_id?: string;
      department_id?: string;
      status?: string;
      priority?: string;
      deadline?: string;
      dependency_task_ids?: string[];
    }
  ): Promise<Task> {
    return request<Task>(`/api/v1/companies/${companyId}/tasks`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getTask(companyId: string, taskId: string): Promise<Task> {
    return request<Task>(`/api/v1/companies/${companyId}/tasks/${taskId}`, {
      method: "GET",
    });
  },

  async updateTask(
    companyId: string,
    taskId: string,
    data: Partial<{
      title: string;
      description: string;
      objective: string;
      project_id: string;
      department_id: string;
      priority: string;
      deadline: string;
    }>
  ): Promise<Task> {
    return request<Task>(`/api/v1/companies/${companyId}/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async updateTaskStatus(
    companyId: string,
    taskId: string,
    data: {
      status: string;
      output?: string;
      error_details?: string;
    }
  ): Promise<Task> {
    return request<Task>(`/api/v1/companies/${companyId}/tasks/${taskId}/status`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async assignTask(
    companyId: string,
    taskId: string,
    data: {
      assigned_to_agent_id?: string;
      assigned_to_user_id?: string;
    }
  ): Promise<Task> {
    return request<Task>(`/api/v1/companies/${companyId}/tasks/${taskId}/assign`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async addTaskDependency(
    companyId: string,
    taskId: string,
    data: {
      depends_on_task_id: string;
    }
  ): Promise<TaskDependency> {
    return request<TaskDependency>(`/api/v1/companies/${companyId}/tasks/${taskId}/dependencies`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async removeTaskDependency(
    companyId: string,
    taskId: string,
    dependsOnTaskId: string
  ): Promise<void> {
    return request<void>(
      `/api/v1/companies/${companyId}/tasks/${taskId}/dependencies/${dependsOnTaskId}`,
      {
        method: "DELETE",
      }
    );
  },

  async deleteTask(companyId: string, taskId: string): Promise<void> {
    return request<void>(`/api/v1/companies/${companyId}/tasks/${taskId}`, {
      method: "DELETE",
    });
  },

  async delegateTask(
    companyId: string,
    taskId: string,
    data: {
      target_agent_id: string;
      reason?: string;
      scope?: string;
      delegator_agent_id?: string;
    }
  ): Promise<DelegationRecord> {
    return request<DelegationRecord>(
      `/api/v1/companies/${companyId}/tasks/${taskId}/delegate`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  async getTaskDelegations(
    companyId: string,
    taskId: string
  ): Promise<DelegationRecord[]> {
    return request<DelegationRecord[]>(
      `/api/v1/companies/${companyId}/tasks/${taskId}/delegations`,
      {
        method: "GET",
      }
    );
  },

  async listCompanyDelegations(
    companyId: string,
    params?: {
      limit?: number;
      offset?: number;
    }
  ): Promise<DelegationListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.limit !== undefined) searchParams.append("limit", params.limit.toString());
    if (params?.offset !== undefined) searchParams.append("offset", params.offset.toString());
    const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return request<DelegationListResponse>(
      `/api/v1/companies/${companyId}/delegations${query}`,
      {
        method: "GET",
      }
    );
  },

  async delegatePlan(
    companyId: string,
    planId: string,
    data?: {
      project_id?: string;
      project_name?: string;
    }
  ): Promise<PlanDelegationResult> {
    return request<PlanDelegationResult>(
      `/api/v1/companies/${companyId}/ceo/plans/${planId}/delegate`,
      {
        method: "POST",
        body: JSON.stringify(data || {}),
      }
    );
  },

  async executeTask(
    companyId: string,
    taskId: string,
    data?: TaskExecuteRequest
  ): Promise<ExecutionRecord> {
    return request<ExecutionRecord>(
      `/api/v1/companies/${companyId}/tasks/${taskId}/execute`,
      {
        method: "POST",
        body: JSON.stringify(data || {}),
      }
    );
  },

  async getTaskExecutions(
    companyId: string,
    taskId: string
  ): Promise<ExecutionListResponse> {
    return request<ExecutionListResponse>(
      `/api/v1/companies/${companyId}/tasks/${taskId}/executions`,
      {
        method: "GET",
      }
    );
  },

  async getExecution(
    companyId: string,
    executionId: string
  ): Promise<ExecutionRecord> {
    return request<ExecutionRecord>(
      `/api/v1/companies/${companyId}/executions/${executionId}`,
      {
        method: "GET",
      }
    );
  },

  async getTools(companyId: string, role?: string): Promise<ToolListResponse> {
    const query = role ? `?role=${encodeURIComponent(role)}` : "";
    return request<ToolListResponse>(`/api/v1/companies/${companyId}/tools${query}`, {
      method: "GET",
    });
  },

  async getToolDefinition(companyId: string, toolName: string): Promise<ToolDefinition> {
    return request<ToolDefinition>(
      `/api/v1/companies/${companyId}/tools/definitions/${encodeURIComponent(toolName)}`,
      {
        method: "GET",
      }
    );
  },

  async executeTool(
    companyId: string,
    payload: ToolExecuteRequest
  ): Promise<ToolExecutionRecord> {
    return request<ToolExecutionRecord>(
      `/api/v1/companies/${companyId}/tools/execute`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async getToolExecutions(
    companyId: string,
    params?: {
      agentId?: string;
      taskId?: string;
      toolName?: string;
      status?: string;
      limit?: number;
      offset?: number;
    }
  ): Promise<ToolExecutionListResponse> {
    const q = new URLSearchParams();
    if (params?.agentId) q.append("agent_id", params.agentId);
    if (params?.taskId) q.append("task_id", params.taskId);
    if (params?.toolName) q.append("tool_name", params.toolName);
    if (params?.status) q.append("status", params.status);
    if (params?.limit) q.append("limit", params.limit.toString());
    if (params?.offset) q.append("offset", params.offset.toString());
    const query = q.toString() ? `?${q.toString()}` : "";
    return request<ToolExecutionListResponse>(
      `/api/v1/companies/${companyId}/tools/executions${query}`,
      {
        method: "GET",
      }
    );
  },

  async getToolExecution(
    companyId: string,
    executionId: string
  ): Promise<ToolExecutionRecord> {
    return request<ToolExecutionRecord>(
      `/api/v1/companies/${companyId}/tools/executions/${executionId}`,
      {
        method: "GET",
      }
    );
  },

  async getApprovals(
    companyId: string,
    params?: {
      status?: string;
      risk_level?: string;
      action_type?: string;
      agent_id?: string;
      limit?: number;
      offset?: number;
    }
  ): Promise<ApprovalListResponse> {
    const q = new URLSearchParams();
    if (params?.status) q.append("status", params.status);
    if (params?.risk_level) q.append("risk_level", params.risk_level);
    if (params?.action_type) q.append("action_type", params.action_type);
    if (params?.agent_id) q.append("agent_id", params.agent_id);
    if (params?.limit) q.append("limit", params.limit.toString());
    if (params?.offset) q.append("offset", params.offset.toString());
    const query = q.toString() ? `?${q.toString()}` : "";
    return request<ApprovalListResponse>(
      `/api/v1/companies/${companyId}/approvals${query}`,
      {
        method: "GET",
      }
    );
  },

  async getApproval(
    companyId: string,
    approvalId: string
  ): Promise<ApprovalRequest> {
    return request<ApprovalRequest>(
      `/api/v1/companies/${companyId}/approvals/${approvalId}`,
      {
        method: "GET",
      }
    );
  },

  async approveRequest(
    companyId: string,
    approvalId: string,
    decision?: ApprovalDecisionRequest
  ): Promise<ApprovalRequest> {
    return request<ApprovalRequest>(
      `/api/v1/companies/${companyId}/approvals/${approvalId}/approve`,
      {
        method: "POST",
        body: JSON.stringify(decision || {}),
      }
    );
  },

  async rejectRequest(
    companyId: string,
    approvalId: string,
    decision?: ApprovalDecisionRequest
  ): Promise<ApprovalRequest> {
    return request<ApprovalRequest>(
      `/api/v1/companies/${companyId}/approvals/${approvalId}/reject`,
      {
        method: "POST",
        body: JSON.stringify(decision || {}),
      }
    );
  },

  async getCompanyState(companyId: string): Promise<CompanyStateResponse> {
    return request<CompanyStateResponse>(
      `/api/v1/companies/${companyId}/memory/state`,
      { method: "GET" }
    );
  },

  async getCompanyDecisions(
    companyId: string,
    statusFilter?: string
  ): Promise<CompanyDecisionListResponse> {
    const q = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : "";
    return request<CompanyDecisionListResponse>(
      `/api/v1/companies/${companyId}/memory/decisions${q}`,
      { method: "GET" }
    );
  },

  async createCompanyDecision(
    companyId: string,
    payload: {
      title: string;
      decision: string;
      rationale: string;
      evidence?: Record<string, unknown>;
      project_id?: string | null;
      task_id?: string | null;
    }
  ): Promise<CompanyDecision> {
    return request<CompanyDecision>(
      `/api/v1/companies/${companyId}/memory/decisions`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async supersedeCompanyDecision(
    companyId: string,
    decisionId: string,
    payload: {
      title: string;
      decision: string;
      rationale: string;
      evidence?: Record<string, unknown>;
      project_id?: string | null;
      task_id?: string | null;
    }
  ): Promise<CompanyDecision> {
    return request<CompanyDecision>(
      `/api/v1/companies/${companyId}/memory/decisions/${decisionId}/supersede`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async inquireCeo(
    companyId: string,
    question: string
  ): Promise<CeoInquiryResponse> {
    return request<CeoInquiryResponse>(
      `/api/v1/companies/${companyId}/ceo/inquire`,
      {
        method: "POST",
        body: JSON.stringify({ question }),
      }
    );
  },

  async getActivity(
    companyId: string,
    params?: ActivityFilters
  ): Promise<ActivityListResponse> {
    const query = new URLSearchParams();
    if (params?.project_id) query.set("project_id", params.project_id);
    if (params?.task_id) query.set("task_id", params.task_id);
    if (params?.actor_type) query.set("actor_type", params.actor_type);
    if (params?.actor_id) query.set("actor_id", params.actor_id);
    if (params?.event_type) query.set("event_type", params.event_type);
    if (params?.search) query.set("search", params.search);
    if (params?.limit) query.set("limit", params.limit.toString());
    if (params?.offset) query.set("offset", params.offset.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<ActivityListResponse>(
      `/api/v1/companies/${companyId}/activity${qs}`,
      { method: "GET" }
    );
  },

  async getProjectActivity(
    companyId: string,
    projectId: string,
    params?: ActivityFilters
  ): Promise<ActivityListResponse> {
    const query = new URLSearchParams();
    if (params?.event_type) query.set("event_type", params.event_type);
    if (params?.search) query.set("search", params.search);
    if (params?.limit) query.set("limit", params.limit.toString());
    if (params?.offset) query.set("offset", params.offset.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<ActivityListResponse>(
      `/api/v1/companies/${companyId}/projects/${projectId}/activity${qs}`,
      { method: "GET" }
    );
  },

  async getTaskActivity(
    companyId: string,
    taskId: string,
    params?: ActivityFilters
  ): Promise<ActivityListResponse> {
    const query = new URLSearchParams();
    if (params?.event_type) query.set("event_type", params.event_type);
    if (params?.search) query.set("search", params.search);
    if (params?.limit) query.set("limit", params.limit.toString());
    if (params?.offset) query.set("offset", params.offset.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<ActivityListResponse>(
      `/api/v1/companies/${companyId}/tasks/${taskId}/activity${qs}`,
      { method: "GET" }
    );
  },

  async getAgentActivity(
    companyId: string,
    agentId: string,
    params?: ActivityFilters
  ): Promise<ActivityListResponse> {
    const query = new URLSearchParams();
    if (params?.event_type) query.set("event_type", params.event_type);
    if (params?.search) query.set("search", params.search);
    if (params?.limit) query.set("limit", params.limit.toString());
    if (params?.offset) query.set("offset", params.offset.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<ActivityListResponse>(
      `/api/v1/companies/${companyId}/agents/${agentId}/activity${qs}`,
      { method: "GET" }
    );
  },

  async getCompanyPresence(
    companyId: string,
    staleThresholdSeconds?: number
  ): Promise<PresenceListResponse> {
    const qs = staleThresholdSeconds
      ? `?stale_threshold_seconds=${staleThresholdSeconds}`
      : "";
    return request<PresenceListResponse>(
      `/api/v1/companies/${companyId}/presence${qs}`,
      { method: "GET" }
    );
  },

  async getPresenceSummary(
    companyId: string,
    staleThresholdSeconds?: number
  ): Promise<PresenceSummary> {
    const qs = staleThresholdSeconds
      ? `?stale_threshold_seconds=${staleThresholdSeconds}`
      : "";
    return request<PresenceSummary>(
      `/api/v1/companies/${companyId}/presence/summary${qs}`,
      { method: "GET" }
    );
  },

  async getAgentPresence(
    companyId: string,
    agentId: string
  ): Promise<AgentPresence> {
    return request<AgentPresence>(
      `/api/v1/companies/${companyId}/agents/${agentId}/presence`,
      { method: "GET" }
    );
  },

  async sendAgentHeartbeat(
    companyId: string,
    agentId: string,
    data: {
      current_step?: string;
      current_activity?: string;
      details?: Record<string, unknown>;
    }
  ): Promise<AgentPresence> {
    return request<AgentPresence>(
      `/api/v1/companies/${companyId}/agents/${agentId}/presence/heartbeat`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  async updateAgentPresence(
    companyId: string,
    agentId: string,
    data: {
      status: PresenceStatus;
      current_activity?: string;
      current_step?: string;
      details?: Record<string, unknown>;
    }
  ): Promise<AgentPresence> {
    return request<AgentPresence>(
      `/api/v1/companies/${companyId}/agents/${agentId}/presence`,
      {
        method: "PATCH",
        body: JSON.stringify(data),
      }
    );
  },

  async getCompanyErrors(
    companyId: string,
    params?: {
      status?: ErrorStatus;
      severity?: ErrorSeverity;
      project_id?: string;
      task_id?: string;
      assigned_to?: string;
      offset?: number;
      limit?: number;
    }
  ): Promise<ErrorListResponse> {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.severity) query.set("severity", params.severity);
    if (params?.project_id) query.set("project_id", params.project_id);
    if (params?.task_id) query.set("task_id", params.task_id);
    if (params?.assigned_to) query.set("assigned_to", params.assigned_to);
    if (params?.offset !== undefined) query.set("offset", params.offset.toString());
    if (params?.limit !== undefined) query.set("limit", params.limit.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<ErrorListResponse>(
      `/api/v1/companies/${companyId}/errors${qs}`,
      { method: "GET" }
    );
  },

  async getCompanyErrorSummary(companyId: string): Promise<ErrorSummary> {
    return request<ErrorSummary>(
      `/api/v1/companies/${companyId}/errors/summary`,
      { method: "GET" }
    );
  },

  async getError(companyId: string, errorId: string): Promise<ErrorRecord> {
    return request<ErrorRecord>(
      `/api/v1/companies/${companyId}/errors/${errorId}`,
      { method: "GET" }
    );
  },

  async createError(
    companyId: string,
    data: ErrorCreatePayload
  ): Promise<ErrorRecord> {
    return request<ErrorRecord>(
      `/api/v1/companies/${companyId}/errors`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  async updateError(
    companyId: string,
    errorId: string,
    data: ErrorUpdatePayload
  ): Promise<ErrorRecord> {
    return request<ErrorRecord>(
      `/api/v1/companies/${companyId}/errors/${errorId}`,
      {
        method: "PATCH",
        body: JSON.stringify(data),
      }
    );
  },

  async assignError(
    companyId: string,
    errorId: string,
    data: ErrorAssignPayload
  ): Promise<ErrorRecord> {
    return request<ErrorRecord>(
      `/api/v1/companies/${companyId}/errors/${errorId}/assign`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  async startErrorInvestigation(
    companyId: string,
    errorId: string,
    investigatedBy?: string
  ): Promise<ErrorRecord> {
    const qs = investigatedBy ? `?investigated_by=${encodeURIComponent(investigatedBy)}` : "";
    return request<ErrorRecord>(
      `/api/v1/companies/${companyId}/errors/${errorId}/investigate${qs}`,
      { method: "POST" }
    );
  },

  async resolveError(
    companyId: string,
    errorId: string,
    data: ErrorResolvePayload
  ): Promise<ErrorRecord> {
    return request<ErrorRecord>(
      `/api/v1/companies/${companyId}/errors/${errorId}/resolve`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  async verifyError(
    companyId: string,
    errorId: string,
    data: ErrorVerifyPayload
  ): Promise<ErrorRecord> {
    return request<ErrorRecord>(
      `/api/v1/companies/${companyId}/errors/${errorId}/verify`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  async reopenError(
    companyId: string,
    errorId: string,
    reason: string
  ): Promise<ErrorRecord> {
    return request<ErrorRecord>(
      `/api/v1/companies/${companyId}/errors/${errorId}/reopen`,
      {
        method: "POST",
        body: JSON.stringify({ reason }),
      }
    );
  },

  async closeError(companyId: string, errorId: string): Promise<ErrorRecord> {
    return request<ErrorRecord>(
      `/api/v1/companies/${companyId}/errors/${errorId}/close`,
      { method: "POST" }
    );
  },

  async getTaskEngineeringView(
    companyId: string,
    taskId: string
  ): Promise<EngineeringTaskView> {
    return request<EngineeringTaskView>(
      `/api/v1/companies/${companyId}/engineering/tasks/${taskId}`
    );
  },

  async upsertEngineeringContext(
    companyId: string,
    taskId: string,
    data: EngineeringContextUpsertPayload
  ): Promise<TaskEngineeringContext> {
    return request<TaskEngineeringContext>(
      `/api/v1/companies/${companyId}/engineering/tasks/${taskId}/context`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      }
    );
  },

  async recordTaskFileChanges(
    companyId: string,
    taskId: string,
    changes: FileChangeCreatePayload[]
  ): Promise<TaskFileChange[]> {
    return request<TaskFileChange[]>(
      `/api/v1/companies/${companyId}/engineering/tasks/${taskId}/files`,
      {
        method: "POST",
        body: JSON.stringify({ changes }),
      }
    );
  },

  async getCompanyFileHistory(
    companyId: string,
    branch?: string,
    limit?: number
  ): Promise<CompanyFileHistoryItem[]> {
    const params = new URLSearchParams();
    if (branch) params.set("branch", branch);
    if (limit) params.set("limit", limit.toString());
    const qs = params.toString() ? `?${params.toString()}` : "";
    return request<CompanyFileHistoryItem[]>(
      `/api/v1/companies/${companyId}/engineering/files${qs}`
    );
  },

  subscribeCompanyEvents(
    companyId: string,
    onEvent: (event: LiveEventPayload) => void,
    onError?: (error: Event) => void
  ): () => void {
    if (typeof EventSource === "undefined") {
      return () => {};
    }

    const url = `${API_BASE_URL}/api/v1/companies/${companyId}/realtime/events`;
    const eventSource = new EventSource(url, { withCredentials: true });

    const normalizeAndDispatch = (dataStr: string, defaultType: string = "system.connected") => {
      try {
        const raw = JSON.parse(dataStr);
        const payload: LiveEventPayload = {
          id: raw.id || `evt-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
          company_id: raw.company_id || companyId,
          event_type: raw.event_type || defaultType,
          message:
            raw.message ||
            raw.summary ||
            (raw.status ? `Status: ${raw.status}` : "Real-time system update"),
          actor_type: raw.actor_type || "SYSTEM",
          actor_id: raw.actor_id ?? null,
          actor_name: raw.actor_name ?? null,
          project_id: raw.project_id ?? null,
          task_id: raw.task_id ?? null,
          metadata: raw.metadata || {},
          timestamp: raw.timestamp || new Date().toISOString(),
        };
        onEvent(payload);
      } catch (err) {
        console.error("Failed to parse SSE event data:", err);
      }
    };

    eventSource.onmessage = (e) => {
      normalizeAndDispatch(e.data);
    };

    const eventTypes = [
      "system.connected",
      "ceo.planning",
      "agent.started",
      "task.assigned",
      "agent.working",
      "tool.called",
      "tool.completed",
      "task.blocked",
      "approval.requested",
      "approval.approved",
      "approval.rejected",
      "error.detected",
      "error.resolved",
      "task.completed",
      "task.status_changed",
      "presence.updated",
      "engineering.verified",
      "engineering.updated",
      "test.pulse",
    ];

    for (const type of eventTypes) {
      eventSource.addEventListener(type, (e: MessageEvent) => {
        normalizeAndDispatch(e.data, type);
      });
    }

    if (onError) {
      eventSource.onerror = onError;
    }

    return () => {
      eventSource.close();
    };
  },

  async emitRealtimeEvent(
    companyId: string,
    payload: RealtimeEmitPayload
  ): Promise<LiveEventPayload> {
    return request<LiveEventPayload>(
      `/api/v1/companies/${companyId}/realtime/emit`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async getRealtimeStatus(companyId: string): Promise<RealtimeStatusResponse> {
    return request<RealtimeStatusResponse>(
      `/api/v1/companies/${companyId}/realtime/status`
    );
  },

  async getCompanyArtifacts(
    companyId: string,
    params?: {
      project_id?: string;
      task_id?: string;
      artifact_type?: string;
      search?: string;
      page?: number;
      page_size?: number;
    }
  ): Promise<ArtifactListResponse> {
    const q = new URLSearchParams();
    if (params?.project_id) q.set("project_id", params.project_id);
    if (params?.task_id) q.set("task_id", params.task_id);
    if (params?.artifact_type) q.set("artifact_type", params.artifact_type);
    if (params?.search) q.set("search", params.search);
    if (params?.page) q.set("page", params.page.toString());
    if (params?.page_size) q.set("page_size", params.page_size.toString());
    const qs = q.toString() ? `?${q.toString()}` : "";
    return request<ArtifactListResponse>(
      `/api/v1/companies/${companyId}/artifacts${qs}`
    );
  },

  async getArtifact(
    companyId: string,
    artifactId: string
  ): Promise<Artifact> {
    return request<Artifact>(
      `/api/v1/companies/${companyId}/artifacts/${artifactId}`
    );
  },

  async createArtifact(
    companyId: string,
    data: ArtifactCreatePayload
  ): Promise<Artifact> {
    return request<Artifact>(
      `/api/v1/companies/${companyId}/artifacts`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  async updateArtifact(
    companyId: string,
    artifactId: string,
    data: ArtifactUpdatePayload
  ): Promise<Artifact> {
    return request<Artifact>(
      `/api/v1/companies/${companyId}/artifacts/${artifactId}`,
      {
        method: "PATCH",
        body: JSON.stringify(data),
      }
    );
  },

  async createArtifactVersion(
    companyId: string,
    artifactId: string,
    data: ArtifactVersionCreatePayload
  ): Promise<Artifact> {
    return request<Artifact>(
      `/api/v1/companies/${companyId}/artifacts/${artifactId}/versions`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  async getArtifactVersions(
    companyId: string,
    artifactId: string
  ): Promise<ArtifactVersionItem[]> {
    return request<ArtifactVersionItem[]>(
      `/api/v1/companies/${companyId}/artifacts/${artifactId}/versions`
    );
  },

  async deleteArtifact(
    companyId: string,
    artifactId: string
  ): Promise<void> {
    return request<void>(
      `/api/v1/companies/${companyId}/artifacts/${artifactId}`,
      {
        method: "DELETE",
      }
    );
  },

  async getCompanyKnowledge(
    companyId: string,
    filters?: {
      category?: string;
      project_id?: string;
      decision_id?: string;
      search?: string;
      page?: number;
      page_size?: number;
    }
  ): Promise<KnowledgeListResponse> {
    const query = new URLSearchParams();
    if (filters?.category) query.set("category", filters.category);
    if (filters?.project_id) query.set("project_id", filters.project_id);
    if (filters?.decision_id) query.set("decision_id", filters.decision_id);
    if (filters?.search) query.set("search", filters.search);
    if (filters?.page) query.set("page", filters.page.toString());
    if (filters?.page_size) query.set("page_size", filters.page_size.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<KnowledgeListResponse>(
      `/api/v1/companies/${companyId}/knowledge${qs}`
    );
  },

  async getKnowledgeItem(
    companyId: string,
    itemId: string
  ): Promise<KnowledgeItem> {
    return request<KnowledgeItem>(
      `/api/v1/companies/${companyId}/knowledge/${itemId}`
    );
  },

  async createKnowledgeItem(
    companyId: string,
    data: KnowledgeCreatePayload
  ): Promise<KnowledgeItem> {
    return request<KnowledgeItem>(
      `/api/v1/companies/${companyId}/knowledge`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  async updateKnowledgeItem(
    companyId: string,
    itemId: string,
    data: KnowledgeUpdatePayload
  ): Promise<KnowledgeItem> {
    return request<KnowledgeItem>(
      `/api/v1/companies/${companyId}/knowledge/${itemId}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      }
    );
  },

  async deleteKnowledgeItem(
    companyId: string,
    itemId: string
  ): Promise<void> {
    return request<void>(
      `/api/v1/companies/${companyId}/knowledge/${itemId}`,
      {
        method: "DELETE",
      }
    );
  },

  async queryCompanyKnowledge(
    companyId: string,
    question: string,
    projectId?: string
  ): Promise<KnowledgeQueryResponse> {
    return request<KnowledgeQueryResponse>(
      `/api/v1/companies/${companyId}/knowledge/query`,
      {
        method: "POST",
        body: JSON.stringify({ question, project_id: projectId }),
      }
    );
  },

  async getSelectiveContext(
    companyId: string,
    payload: {
      task_id?: string;
      project_id?: string;
      intent_keywords?: string[];
      max_items?: number;
    }
  ): Promise<SelectiveContextResponse> {
    return request<SelectiveContextResponse>(
      `/api/v1/companies/${companyId}/knowledge/context`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  // Phase 20 — Semantic / Vector Memory
  async searchSemanticMemory(
    companyId: string,
    payload: SemanticSearchRequest
  ): Promise<SemanticSearchResponse> {
    return request<SemanticSearchResponse>(
      `/api/v1/companies/${companyId}/semantic/search`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async buildSemanticContext(
    companyId: string,
    payload: SemanticContextBuildRequest
  ): Promise<SemanticContextBuildResponse> {
    return request<SemanticContextBuildResponse>(
      `/api/v1/companies/${companyId}/semantic/context`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async batchIndexMemory(
    companyId: string,
    payload: BatchIndexRequest = {}
  ): Promise<BatchIndexResponse> {
    return request<BatchIndexResponse>(
      `/api/v1/companies/${companyId}/semantic/index`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async getVectorMemoryStats(
    companyId: string
  ): Promise<VectorMemoryStatsResponse> {
    return request<VectorMemoryStatsResponse>(
      `/api/v1/companies/${companyId}/semantic/stats`
    );
  },

  // Phase 21 — Voice Interface
  async createVoiceSession(
    companyId: string,
    payload?: VoiceSessionCreatePayload
  ): Promise<VoiceSessionResponse> {
    return request<VoiceSessionResponse>(
      `/api/v1/companies/${companyId}/voice/sessions`,
      {
        method: "POST",
        body: JSON.stringify(payload || {}),
      }
    );
  },

  async listVoiceSessions(
    companyId: string,
    limit: number = 20
  ): Promise<VoiceSessionListResponse> {
    return request<VoiceSessionListResponse>(
      `/api/v1/companies/${companyId}/voice/sessions?limit=${limit}`
    );
  },

  async getVoiceSession(
    companyId: string,
    sessionId: string
  ): Promise<VoiceSessionResponse> {
    return request<VoiceSessionResponse>(
      `/api/v1/companies/${companyId}/voice/sessions/${sessionId}`
    );
  },

  async sendVoiceCommand(
    companyId: string,
    payload: VoiceCommandPayload
  ): Promise<VoiceCommandResponse> {
    return request<VoiceCommandResponse>(
      `/api/v1/companies/${companyId}/voice/command`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async synthesizeVoiceSpeech(
    companyId: string,
    payload: VoiceSynthesizeRequest
  ): Promise<VoiceSynthesizeResponse> {
    return request<VoiceSynthesizeResponse>(
      `/api/v1/companies/${companyId}/voice/synthesize`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async getVoiceTelemetry(
    companyId: string
  ): Promise<VoiceTelemetryResponse> {
    return request<VoiceTelemetryResponse>(
      `/api/v1/companies/${companyId}/voice/telemetry`
    );
  },

  // Phase 22 — Verification & AI Evaluation
  async verifyTask(
    companyId: string,
    taskId: string,
    payload?: TaskVerificationPayload
  ): Promise<VerificationRunResponse> {
    return request<VerificationRunResponse>(
      `/api/v1/companies/${companyId}/verification/verify/task/${taskId}`,
      {
        method: "POST",
        body: JSON.stringify(payload || {}),
      }
    );
  },

  async verifyArtifact(
    companyId: string,
    artifactId: string,
    payload?: ArtifactVerificationPayload
  ): Promise<VerificationRunResponse> {
    return request<VerificationRunResponse>(
      `/api/v1/companies/${companyId}/verification/verify/artifact/${artifactId}`,
      {
        method: "POST",
        body: JSON.stringify(payload || {}),
      }
    );
  },

  async runEvaluationBenchmark(
    companyId: string,
    payload: BenchmarkRunRequestPayload
  ): Promise<BenchmarkRunResponse> {
    return request<BenchmarkRunResponse>(
      `/api/v1/companies/${companyId}/verification/benchmarks/run`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async listBenchmarks(
    companyId: string,
    category?: string
  ): Promise<BenchmarkDefinitionResponse[]> {
    const query = category ? `?category=${encodeURIComponent(category)}` : "";
    return request<BenchmarkDefinitionResponse[]>(
      `/api/v1/companies/${companyId}/verification/benchmarks${query}`
    );
  },

  async listVerificationRuns(
    companyId: string,
    params?: {
      target_type?: string;
      target_id?: string;
      status?: string;
      limit?: number;
      offset?: number;
    }
  ): Promise<VerificationRunListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.target_type) searchParams.set("target_type", params.target_type);
    if (params?.target_id) searchParams.set("target_id", params.target_id);
    if (params?.status) searchParams.set("status", params.status);
    if (params?.limit !== undefined) searchParams.set("limit", String(params.limit));
    if (params?.offset !== undefined) searchParams.set("offset", String(params.offset));
    const qs = searchParams.toString();
    return request<VerificationRunListResponse>(
      `/api/v1/companies/${companyId}/verification/runs${qs ? `?${qs}` : ""}`
    );
  },

  async getVerificationRun(
    companyId: string,
    runId: string
  ): Promise<VerificationRunResponse> {
    return request<VerificationRunResponse>(
      `/api/v1/companies/${companyId}/verification/runs/${runId}`
    );
  },

  async getVerificationTelemetry(
    companyId: string
  ): Promise<VerificationTelemetryResponse> {
    return request<VerificationTelemetryResponse>(
      `/api/v1/companies/${companyId}/verification/telemetry`
    );
  },
};

export const apiClient = api;

export type PresenceStatus =
  | "ONLINE"
  | "IDLE"
  | "WORKING"
  | "WAITING"
  | "BLOCKED"
  | "ERROR"
  | "OFFLINE";

export interface AgentPresence {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_role: string;
  department_id?: string | null;
  department_name?: string | null;
  company_id: string;
  status: PresenceStatus;
  current_task_id?: string | null;
  current_task_title?: string | null;
  current_project_id?: string | null;
  current_project_name?: string | null;
  current_activity?: string | null;
  current_step?: string | null;
  last_heartbeat_at: string;
  started_at?: string | null;
  updated_at: string;
  duration_seconds: number;
  is_stale: boolean;
  details: Record<string, unknown>;
}

export interface PresenceListResponse {
  items: AgentPresence[];
  total: number;
}

export interface PresenceSummary {
  total_agents: number;
  working_count: number;
  idle_count: number;
  waiting_count: number;
  blocked_count: number;
  error_count: number;
  offline_count: number;
}

export interface ActivityEvent {
  id: string;
  company_id: string;
  project_id?: string | null;
  task_id?: string | null;
  actor_type: string;
  actor_id?: string | null;
  event_type: string;
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ActivityListResponse {
  items: ActivityEvent[];
  total: number;
  limit: number;
  offset: number;
}

export interface ActivityFilters {
  project_id?: string;
  task_id?: string;
  actor_type?: string;
  actor_id?: string;
  event_type?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

export interface CompanyDecision {
  id: string;
  company_id: string;
  project_id?: string | null;
  task_id?: string | null;
  title: string;
  decision: string;
  rationale: string;
  evidence: Record<string, unknown>;
  status: "ACTIVE" | "SUPERSEDED" | "REVOKED";
  decided_by_user_id?: string | null;
  decided_by_agent_id?: string | null;
  superseded_by_decision_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CompanyDecisionListResponse {
  items: CompanyDecision[];
  total: number;
}

export interface CompanyStateResponse {
  company: {
    id: string;
    name: string;
    mission?: string | null;
    description?: string | null;
    created_at?: string | null;
  };
  departments: Array<{
    id: string;
    name: string;
    description?: string | null;
    created_at?: string | null;
  }>;
  agents: Array<{
    id: string;
    name: string;
    role: string;
    department_id?: string | null;
    status: string;
    authority_level: string;
  }>;
  projects: Array<{
    id: string;
    name: string;
    status: string;
    priority: string;
    objective?: string | null;
    description?: string | null;
  }>;
  tasks_summary: {
    total: number;
    by_status: Record<string, number>;
    recent_active_tasks: Array<{
      id: string;
      title: string;
      status: string;
      priority: string;
    }>;
  };
  recent_approvals: Array<{
    id: string;
    action_type: string;
    risk_level: string;
    status: string;
    description: string;
  }>;
  decisions: Array<{
    id: string;
    title: string;
    decision: string;
    rationale: string;
    status: string;
    superseded_by_decision_id?: string | null;
    created_at?: string | null;
  }>;
  generated_at: string;
}

export interface CeoInquiryCitation {
  source_type: string;
  source_id: string;
  reference: string;
}

export interface CeoInquiryResponse {
  answer: string;
  citations: CeoInquiryCitation[];
  grounded_state_timestamp: string;
}

export type ErrorSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export type ErrorStatus =
  | "OPEN"
  | "TRIAGED"
  | "ASSIGNED"
  | "INVESTIGATING"
  | "BLOCKED"
  | "RESOLVED"
  | "VERIFYING"
  | "VERIFIED"
  | "REOPENED"
  | "CLOSED";

export interface ErrorRecord {
  id: string;
  company_id: string;
  project_id?: string | null;
  project_name?: string | null;
  task_id?: string | null;
  task_title?: string | null;
  title: string;
  description?: string | null;
  severity: ErrorSeverity;
  status: ErrorStatus;
  detected_by: string;
  assigned_to?: string | null;
  investigated_by?: string | null;
  resolved_by?: string | null;
  verified_by?: string | null;
  assigned_agent_id?: string | null;
  assigned_agent_name?: string | null;
  assigned_user_id?: string | null;
  assigned_user_name?: string | null;
  root_cause?: string | null;
  resolution?: string | null;
  evidence: Record<string, unknown>;
  created_at: string;
  resolved_at?: string | null;
  verified_at?: string | null;
}

export interface ErrorListResponse {
  items: ErrorRecord[];
  total: number;
  open_count: number;
  investigating_count: number;
  resolved_count: number;
  verified_count: number;
}

export interface ErrorSummary {
  total_errors: number;
  open_count: number;
  triaged_count: number;
  assigned_count: number;
  investigating_count: number;
  blocked_count: number;
  resolved_count: number;
  verifying_count: number;
  verified_count: number;
  reopened_count: number;
  closed_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
}

export interface ErrorCreatePayload {
  title: string;
  description?: string | null;
  severity?: ErrorSeverity;
  detected_by: string;
  project_id?: string | null;
  task_id?: string | null;
  assigned_to?: string | null;
  assigned_agent_id?: string | null;
  assigned_user_id?: string | null;
  evidence?: Record<string, unknown>;
}

export interface ErrorUpdatePayload {
  title?: string;
  description?: string | null;
  severity?: ErrorSeverity;
  status?: ErrorStatus;
  assigned_to?: string | null;
  assigned_agent_id?: string | null;
  assigned_user_id?: string | null;
  investigated_by?: string | null;
  resolved_by?: string | null;
  verified_by?: string | null;
  root_cause?: string | null;
  resolution?: string | null;
  evidence?: Record<string, unknown>;
}

export interface ErrorAssignPayload {
  assigned_to: string;
  assigned_agent_id?: string | null;
  assigned_user_id?: string | null;
}

export interface ErrorResolvePayload {
  resolved_by: string;
  resolution: string;
  root_cause?: string | null;
  evidence?: Record<string, unknown>;
}

export interface ErrorVerifyPayload {
  verified_by: string;
  evidence: Record<string, unknown>;
  close_immediately?: boolean;
}

export type TestStatus = "PENDING" | "RUNNING" | "PASSED" | "FAILED" | "SKIPPED";
export type VerificationState = "PENDING" | "IN_REVIEW" | "VERIFIED" | "REJECTED";
export type FileChangeType = "ADDED" | "MODIFIED" | "DELETED" | "RENAMED";

export interface TaskEngineeringContext {
  id: string;
  company_id: string;
  task_id: string;
  repository: string;
  branch: string;
  pull_request_number?: string | null;
  pull_request_url?: string | null;
  pull_request_title?: string | null;
  commit_count: number;
  test_status: TestStatus | string;
  test_output_summary?: string | null;
  verification_state: VerificationState | string;
  verification_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskFileChange {
  id: string;
  company_id: string;
  task_id: string;
  file_path: string;
  repository: string;
  branch: string;
  agent_id?: string | null;
  agent_name: string;
  change_type: FileChangeType | string;
  commit_hash?: string | null;
  commit_message?: string | null;
  additions: number;
  deletions: number;
  change_summary?: string | null;
  last_modified_at: string;
  created_at: string;
}

export interface EngineeringTaskView {
  task_id: string;
  company_id: string;
  context?: TaskEngineeringContext | null;
  file_changes: TaskFileChange[];
  total_files_changed: number;
  total_additions: number;
  total_deletions: number;
}

export interface CompanyFileHistoryItem {
  file_path: string;
  repository: string;
  branches: string[];
  change_count: number;
  last_modified_at: string;
  last_commit_hash?: string | null;
  last_agent_id?: string | null;
  last_agent_name?: string | null;
}

export interface EngineeringContextUpsertPayload {
  repository?: string;
  branch?: string;
  pull_request_number?: string | null;
  pull_request_url?: string | null;
  pull_request_title?: string | null;
  commit_count?: number;
  test_status?: TestStatus;
  test_output_summary?: string | null;
  verification_state?: VerificationState;
  verification_notes?: string | null;
}

export interface FileChangeCreatePayload {
  file_path: string;
  repository?: string;
  branch?: string;
  agent_id?: string | null;
  agent_name?: string | null;
  change_type?: FileChangeType;
  commit_hash?: string | null;
  commit_message?: string | null;
  additions?: number;
  deletions?: number;
  change_summary?: string | null;
}

export type RealtimeEventType =
  | "ceo.planning"
  | "agent.started"
  | "task.assigned"
  | "agent.working"
  | "tool.called"
  | "tool.completed"
  | "task.blocked"
  | "approval.requested"
  | "approval.approved"
  | "approval.rejected"
  | "error.detected"
  | "error.resolved"
  | "task.completed"
  | "task.status_changed"
  | "presence.updated"
  | "engineering.verified"
  | "engineering.updated"
  | "system.connected"
  | "system.heartbeat"
  | "test.pulse";

export interface LiveEventPayload {
  id: string;
  company_id: string;
  event_type: RealtimeEventType | string;
  message: string;
  actor_type: string;
  actor_id?: string | null;
  actor_name?: string | null;
  project_id?: string | null;
  task_id?: string | null;
  metadata?: Record<string, unknown>;
  timestamp: string;
}

export interface RealtimeStatusResponse {
  company_id: string;
  active_subscribers: number;
  channel_status: "active" | "idle";
  events_dispatched: number;
  timestamp: string;
}

export interface RealtimeEmitPayload {
  event_type: string;
  message: string;
  actor_type?: string;
  actor_id?: string | null;
  actor_name?: string | null;
  project_id?: string | null;
  task_id?: string | null;
  metadata?: Record<string, unknown>;
}

export type ArtifactType =
  | "MARKDOWN"
  | "TEXT"
  | "PDF"
  | "CSV"
  | "JSON"
  | "IMAGE"
  | "CODE"
  | "REPORT"
  | "DOCUMENT";

export interface Artifact {
  id: string;
  company_id: string;
  project_id?: string | null;
  task_id?: string | null;
  created_by_agent_id?: string | null;
  created_by_user_id?: string | null;
  creator_name: string;
  name: string;
  artifact_type: ArtifactType | string;
  version: number;
  parent_artifact_id?: string | null;
  location?: string | null;
  content?: string | null;
  file_size_bytes: number;
  change_summary?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ArtifactVersionItem {
  id: string;
  version: number;
  creator_name: string;
  change_summary?: string | null;
  file_size_bytes: number;
  created_at: string;
  parent_artifact_id?: string | null;
}

export interface ArtifactListResponse {
  items: Artifact[];
  total: number;
  page: number;
  page_size: number;
}

export interface ArtifactCreatePayload {
  name: string;
  artifact_type?: ArtifactType | string;
  project_id?: string | null;
  task_id?: string | null;
  creator_name?: string | null;
  created_by_agent_id?: string | null;
  created_by_user_id?: string | null;
  location?: string | null;
  content?: string | null;
  file_size_bytes?: number | null;
  change_summary?: string | null;
  metadata?: Record<string, unknown>;
}

export interface ArtifactUpdatePayload {
  name?: string;
  artifact_type?: ArtifactType | string;
  project_id?: string | null;
  task_id?: string | null;
  location?: string | null;
  content?: string | null;
  file_size_bytes?: number | null;
  change_summary?: string | null;
  metadata?: Record<string, unknown>;
}

export interface ArtifactVersionCreatePayload {
  content?: string | null;
  location?: string | null;
  change_summary: string;
  creator_name?: string | null;
  created_by_agent_id?: string | null;
  created_by_user_id?: string | null;
  file_size_bytes?: number | null;
  metadata?: Record<string, unknown>;
}

export type KnowledgeCategory =
  | "STRATEGY"
  | "RESEARCH"
  | "POLICY"
  | "DECISION_RATIONALE"
  | "PROCEDURE"
  | "MEETING_NOTE"
  | "HISTORICAL_RESULT"
  | "GENERAL";

export type KnowledgeSourceType =
  | "USER"
  | "AGENT"
  | "DOCUMENT"
  | "RESEARCH"
  | "MEETING"
  | "POST_MORTEM"
  | "EXTERNAL"
  | "SYSTEM";

export type KnowledgeConfidence = "HIGH" | "MEDIUM" | "LOW" | "ESTIMATED";

export interface KnowledgeItem {
  id: string;
  company_id: string;
  project_id?: string | null;
  task_id?: string | null;
  decision_id?: string | null;
  artifact_id?: string | null;
  title: string;
  category: KnowledgeCategory | string;
  content: string;
  source_type: KnowledgeSourceType | string;
  source_uri?: string | null;
  author_name: string;
  confidence: KnowledgeConfidence | string;
  tags: string[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeListResponse {
  items: KnowledgeItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface KnowledgeCreatePayload {
  title: string;
  category?: KnowledgeCategory | string;
  content: string;
  project_id?: string | null;
  task_id?: string | null;
  decision_id?: string | null;
  artifact_id?: string | null;
  source_type?: KnowledgeSourceType | string;
  source_uri?: string | null;
  author_name?: string | null;
  confidence?: KnowledgeConfidence | string;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface KnowledgeUpdatePayload {
  title?: string;
  category?: KnowledgeCategory | string;
  content?: string;
  project_id?: string | null;
  task_id?: string | null;
  decision_id?: string | null;
  artifact_id?: string | null;
  source_type?: KnowledgeSourceType | string;
  source_uri?: string | null;
  author_name?: string | null;
  confidence?: KnowledgeConfidence | string;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface KnowledgeQueryCitation {
  source_type: string;
  source_id: string;
  title: string;
  reference: string;
  confidence: string;
}

export interface KnowledgeQueryResponse {
  question: string;
  answer: string;
  canonical_topic?: string | null;
  citations: KnowledgeQueryCitation[];
  related_decisions: Record<string, unknown>[];
  related_artifacts: Record<string, unknown>[];
  timestamp: string;
}

export interface SelectiveContextResponse {
  company_id: string;
  project?: Record<string, unknown> | null;
  task?: Record<string, unknown> | null;
  relevant_decisions: Record<string, unknown>[];
  relevant_knowledge: KnowledgeItem[];
  relevant_artifacts: Record<string, unknown>[];
  historical_results_summary: Record<string, unknown>[];
  synthesized_context: string;
  item_count: number;
  timestamp: string;
}

// Phase 20 — Semantic / Vector Memory Interfaces
export interface SemanticSearchRequest {
  query: string;
  limit?: number;
  min_similarity?: number;
  source_types?: string[];
  project_id?: string | null;
}

export interface SemanticSearchResultItem {
  id: string;
  source_type: string;
  source_id: string;
  title: string;
  content_chunk: string;
  similarity_score: number;
  distance: number;
  metadata: Record<string, unknown>;
}

export interface SemanticSearchResponse {
  query: string;
  results: SemanticSearchResultItem[];
  total_matches: number;
  execution_time_ms: number;
  timestamp: string;
}

export interface SemanticContextBuildRequest {
  query: string;
  task_id?: string | null;
  project_id?: string | null;
  limit?: number;
  min_similarity?: number;
}

export interface SemanticContextBuildResponse {
  query: string;
  company_id: string;
  synthesized_context: string;
  items_used: SemanticSearchResultItem[];
  total_items: number;
  timestamp: string;
}

export interface VectorMemoryStatsResponse {
  company_id: string;
  total_embeddings: number;
  count_by_source: Record<string, number>;
  dimension: number;
  vector_engine: string;
  index_type: string;
  timestamp: string;
}

export interface BatchIndexRequest {
  source_types?: string[];
  force_reindex?: boolean;
}

export interface BatchIndexResponse {
  company_id: string;
  indexed_count: number;
  updated_count: number;
  skipped_count: number;
  total_chunks: number;
  duration_ms: number;
  timestamp: string;
}

// Phase 21 — Voice Interface Interfaces adhering to docs/Phases.md Section 25 and docs/Memory.md Section 60
export type VoiceState =
  | "LISTENING"
  | "PROCESSING"
  | "PLANNING"
  | "EXECUTING"
  | "WAITING_FOR_APPROVAL"
  | "SPEAKING"
  | "IDLE";

export type VoiceIntent =
  | "STATUS_QUERY"
  | "TASK_CREATE"
  | "TASK_CONTROL"
  | "APPROVAL_DECISION"
  | "DELEGATION_COMMAND"
  | "GENERAL_INQUIRY";

export interface VoiceInteractionItem {
  id: string;
  session_id: string;
  company_id: string;
  user_id: string;
  transcript: string;
  intent: VoiceIntent;
  action_taken?: string | null;
  action_entity_id?: string | null;
  action_success: boolean;
  spoken_response: string;
  detailed_response: string;
  execution_time_ms: number;
  created_at: string;
}

export interface VoiceSessionResponse {
  id: string;
  company_id: string;
  user_id: string;
  title: string;
  state: VoiceState;
  context_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  interactions: VoiceInteractionItem[];
}

export interface VoiceSessionListResponse {
  items: VoiceSessionResponse[];
  total: number;
}

export interface VoiceSessionCreatePayload {
  title?: string;
  initial_context?: Record<string, unknown>;
}

export interface VoiceCommandPayload {
  transcript: string;
  session_id?: string | null;
  context_task_id?: string | null;
  project_id?: string | null;
  language?: string | null;
}

export interface VoiceCommandResponse {
  session_id: string;
  transcript: string;
  intent: VoiceIntent;
  state: VoiceState;
  spoken_response: string;
  detailed_response: string;
  action_taken?: string | null;
  action_entity_id?: string | null;
  action_success: boolean;
  execution_time_ms: number;
  timestamp: string;
}

export interface VoiceSynthesizeRequest {
  text: string;
  voice_id?: string;
}

export interface VoiceSynthesizeResponse {
  text: string;
  audio_format: string;
  audio_b64?: string | null;
  phonemes?: string | null;
}

export interface VoiceTelemetryResponse {
  company_id: string;
  total_sessions: number;
  total_interactions: number;
  intent_distribution: Record<string, number>;
  avg_execution_time_ms: number;
  last_interaction_at?: string | null;
  timestamp: string;
}

// Phase 22 — Verification & AI Evaluation Interfaces adhering to docs/Phases.md Section 26, docs/Architecture.md Sections 71-72, and docs/Rules.md Sections 17 & 146
export type CriterionType =
  | "CORRECTNESS"
  | "COMPLETENESS"
  | "TOOL_USAGE"
  | "PERMISSION_COMPLIANCE"
  | "HALLUCINATION_RATE"
  | "INSTRUCTION_FOLLOWING"
  | "TASK_COMPLETION"
  | "EVIDENCE_QUALITY";

export type VerificationStatus = "RUNNING" | "PASSED" | "FAILED" | "WARNING";

export type PipelineStage =
  | "SCHEMA_VALIDATION"
  | "EVIDENCE_CHECK"
  | "TASK_VERIFICATION"
  | "EVALUATION"
  | "COMPLETED";

export type BenchmarkCategory =
  | "CEO"
  | "MARKETING"
  | "ENGINEERING"
  | "SALES"
  | "TOOL"
  | "APPROVAL"
  | "FAILURE"
  | "RECOVERY";

export interface CriterionScoreItem {
  id: string;
  run_id: string;
  criterion: CriterionType;
  score: number;
  status: VerificationStatus;
  details?: string | null;
  evidence?: Record<string, unknown> | null;
  created_at: string;
}

export interface VerificationRunResponse {
  id: string;
  company_id: string;
  target_type: "TASK" | "ARTIFACT" | "BENCHMARK" | string;
  target_id: string;
  agent_id?: string | null;
  status: VerificationStatus;
  overall_score: number;
  pipeline_stage: PipelineStage;
  summary?: string | null;
  evaluation_metadata?: Record<string, unknown> | null;
  started_at: string;
  completed_at?: string | null;
  criteria_scores: CriterionScoreItem[];
}

export interface VerificationRunListResponse {
  items: VerificationRunResponse[];
  total: number;
}

export interface TaskVerificationPayload {
  criteria_overrides?: Record<string, unknown>;
}

export interface ArtifactVerificationPayload {
  criteria_overrides?: Record<string, unknown>;
}

export interface BenchmarkRunRequestPayload {
  category: BenchmarkCategory;
  prompt: string;
  agent_id?: string | null;
  timeout_seconds?: number;
}

export interface BenchmarkDefinitionResponse {
  id: string;
  company_id: string;
  name: string;
  category: BenchmarkCategory;
  description: string;
  canonical_prompt: string;
  expected_criteria: string[];
  passing_threshold: number;
  is_active: boolean;
  created_at: string;
}

export interface BenchmarkRunResponse {
  benchmark_id: string;
  benchmark_name: string;
  category: BenchmarkCategory;
  verification_run: VerificationRunResponse;
  passed: boolean;
}

export interface VerificationTelemetryResponse {
  company_id: string;
  total_runs: number;
  passed_runs: number;
  failed_runs: number;
  pass_rate_percent: number;
  avg_overall_score: number;
  avg_scores_by_criterion: Record<string, number>;
  active_benchmarks_count: number;
  timestamp: string;
}

