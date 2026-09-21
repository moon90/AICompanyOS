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
};
