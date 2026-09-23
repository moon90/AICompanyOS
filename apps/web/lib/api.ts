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
};

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



