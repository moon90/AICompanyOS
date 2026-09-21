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
};
