import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { api } from "./api";

describe("Web API Client", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("getMe returns authenticated user on 200 OK", async () => {
    const mockUser = {
      id: "user-123",
      name: "Test Operator",
      email: "operator@company.os",
      status: "active",
      created_at: "2026-09-21T00:00:00Z",
      last_login_at: null,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockUser,
    } as Response);

    const user = await api.getMe();
    expect(user).toEqual(mockUser);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/auth/me",
      expect.objectContaining({
        method: "GET",
        credentials: "include",
      })
    );
  });

  it("getSystemStatus returns live infrastructure telemetry", async () => {
    const mockStatus = {
      status: "operational",
      database: "connected",
      auth_authority: "postgresql_sessions",
      environment: "test",
      version: "0.1.0",
      current_phase: "Phase 4 — Agent Registry",
      timestamp: "2026-09-21T00:00:00Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockStatus,
    } as Response);

    const status = await api.getSystemStatus();
    expect(status).toEqual(mockStatus);
    expect(status.current_phase).toBe("Phase 4 — Agent Registry");
  });

  it("getCompanies returns list of user companies", async () => {
    const mockCompanies = [
      {
        id: "comp-1",
        name: "Acme Corp",
        description: "Building the future",
        mission: "Scale AI",
        industry: "Technology",
        status: "active",
        created_at: "2026-09-21T00:00:00Z",
        updated_at: "2026-09-21T00:00:00Z",
        user_role: "owner",
      },
    ];

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockCompanies,
    } as Response);

    const companies = await api.getCompanies();
    expect(companies).toHaveLength(1);
    expect(companies[0].name).toBe("Acme Corp");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies",
      expect.objectContaining({
        method: "GET",
        credentials: "include",
      })
    );
  });

  it("createCompany sends POST with company payload", async () => {
    const mockCompany = {
      id: "comp-2",
      name: "New Co",
      description: null,
      mission: null,
      industry: null,
      status: "active",
      created_at: "2026-09-21T00:00:00Z",
      updated_at: "2026-09-21T00:00:00Z",
      user_role: "owner",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockCompany,
    } as Response);

    const result = await api.createCompany({ name: "New Co" });
    expect(result.name).toBe("New Co");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ name: "New Co" }),
      })
    );
  });

  it("getDepartments returns company departments", async () => {
    const mockDepartments = [
      {
        id: "dept-1",
        company_id: "comp-1",
        name: "Technology & Engineering",
        code: "CTO",
        description: "Software engineering",
        lead_role: "CTO",
        status: "active",
        created_at: "2026-09-21T00:00:00Z",
        updated_at: "2026-09-21T00:00:00Z",
      },
    ];

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockDepartments,
    } as Response);

    const depts = await api.getDepartments("comp-1");
    expect(depts).toHaveLength(1);
    expect(depts[0].code).toBe("CTO");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/departments",
      expect.objectContaining({
        method: "GET",
        credentials: "include",
      })
    );
  });

  it("getAgents returns company agents", async () => {
    const mockAgents = [
      {
        id: "agent-1",
        company_id: "comp-1",
        department_id: "dept-1",
        department_name: "Technology",
        department_code: "CTO",
        name: "Chief Technology Officer",
        role: "cto",
        type: "executive",
        reports_to: null,
        manager_name: null,
        mission: "Architect systems",
        status: "active",
        authority_level: 4,
        created_at: "2026-09-21T00:00:00Z",
        updated_at: "2026-09-21T00:00:00Z",
        current_version: "1.0",
        current_model: "gemini-2.0-flash",
      },
    ];

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockAgents,
    } as Response);

    const agents = await api.getAgents("comp-1");
    expect(agents).toHaveLength(1);
    expect(agents[0].name).toBe("Chief Technology Officer");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/agents",
      expect.objectContaining({
        method: "GET",
        credentials: "include",
      })
    );
  });

  it("createAgent sends POST with agent registration payload", async () => {
    const mockCreated = {
      id: "agent-2",
      company_id: "comp-1",
      department_id: "dept-1",
      department_name: "Technology",
      department_code: "CTO",
      name: "Software Engineer",
      role: "engineer",
      type: "worker",
      reports_to: "agent-1",
      manager_name: "CTO",
      mission: "Write code",
      status: "active",
      authority_level: 2,
      created_at: "2026-09-21T00:00:00Z",
      updated_at: "2026-09-21T00:00:00Z",
      current_version: "1.0",
      current_model: "gemini-2.0-flash",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockCreated,
    } as Response);

    const payload = {
      department_id: "dept-1",
      name: "Software Engineer",
      role: "engineer",
      type: "worker" as const,
      reports_to: "agent-1",
      mission: "Write code",
      authority_level: 2,
      model: "gemini-2.0-flash",
      system_prompt: "You write code.",
      capabilities: ["coding"],
      tools: ["github"],
      configuration: {},
    };

    const result = await api.createAgent("comp-1", payload);
    expect(result.name).toBe("Software Engineer");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/agents",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify(payload),
      })
    );
  });

  it("provisionDefaultAgents calls POST provision endpoint", async () => {
    const mockProvisioned = [
      {
        id: "agent-1",
        company_id: "comp-1",
        department_id: "dept-1",
        department_name: "Executive",
        department_code: "EXEC",
        name: "Chief Executive Officer",
        role: "ceo",
        type: "executive",
        reports_to: null,
        manager_name: null,
        mission: "Direct company",
        status: "active",
        authority_level: 5,
        created_at: "2026-09-21T00:00:00Z",
        updated_at: "2026-09-21T00:00:00Z",
        current_version: "1.0",
        current_model: "gemini-2.0-flash",
      },
    ];

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockProvisioned,
    } as Response);

    const result = await api.provisionDefaultAgents("comp-1");
    expect(result).toHaveLength(1);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/agents/provision-defaults",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      })
    );
  });

  it("createAgentDefinition calls POST definitions endpoint", async () => {
    const mockDef = {
      id: "def-2",
      agent_id: "agent-1",
      version: "1.1",
      system_prompt: "Updated prompt",
      model: "gemini-2.0-pro",
      capabilities: ["coding", "review"],
      tools: ["github"],
      configuration: {},
      is_current: true,
      created_at: "2026-09-21T00:00:00Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockDef,
    } as Response);

    const result = await api.createAgentDefinition("comp-1", "agent-1", {
      version: "1.1",
      system_prompt: "Updated prompt",
      model: "gemini-2.0-pro",
      capabilities: ["coding", "review"],
      tools: ["github"],
      configuration: {},
      set_as_current: true,
    });

    expect(result.version).toBe("1.1");
    expect(result.model).toBe("gemini-2.0-pro");
  });

  it("throws ApiError when response is not ok", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: async () => ({ detail: "Authentication required." }),
    } as Response);

    await expect(api.getMe()).rejects.toMatchObject({
      status: 401,
      detail: "Authentication required.",
    });
  });
});
