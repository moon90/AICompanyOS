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
      current_phase: "Phase 5 — CEO Orchestrator Foundation",
      timestamp: "2026-09-21T00:00:00Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockStatus,
    } as Response);

    const status = await api.getSystemStatus();
    expect(status).toEqual(mockStatus);
    expect(status.current_phase).toBe("Phase 5 — CEO Orchestrator Foundation");
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

  it("getCeoContext returns company context and CEO identity", async () => {
    const mockContext = {
      company: {
        id: "comp-1",
        name: "Acme Corp",
        description: "AI Company",
        mission: "Build future",
        industry: "Tech",
        status: "active",
      },
      ceo_agent: {
        id: "ceo-1",
        name: "Chief Executive Officer",
        role: "ceo",
        authority_level: "executive",
        status: "active",
      },
      departments: [],
      agents: [],
      agent_count: 11,
      department_count: 5,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockContext,
    } as Response);

    const ctx = await api.getCeoContext("comp-1");
    expect(ctx.company.name).toBe("Acme Corp");
    expect(ctx.ceo_agent?.role).toBe("ceo");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/ceo/context",
      expect.objectContaining({
        method: "GET",
        credentials: "include",
      })
    );
  });

  it("createPlan sends POST to plan endpoint with goal payload", async () => {
    const mockPlanDetail = {
      id: "plan-1",
      company_id: "comp-1",
      user_id: "user-1",
      ceo_agent_id: "ceo-1",
      goal: "Expand to Europe",
      requested_outcome: "Analysis report",
      priority: "high",
      status: "proposed",
      reasoning_summary: "Strategic 4-step decomposition",
      context_snapshot: {},
      plan_steps: [
        {
          step_id: "step_1",
          title: "Discovery",
          description: "Analyze market",
          assigned_agent_id: "ag-1",
          assigned_agent_role: "researcher",
          department_code: "SALES",
          depends_on: [],
          required_capabilities: ["research"],
          expected_output: "Report",
          verification_criteria: "Complete",
        },
      ],
      delegation_proposals: [],
      approval_requirements: [],
      risks: [],
      assumptions: [],
      created_at: "2026-09-21T00:00:00Z",
      updated_at: "2026-09-21T00:00:00Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockPlanDetail,
    } as Response);

    const payload = {
      objective: "Expand to Europe",
      requested_outcome: "Analysis report",
      priority: "high" as const,
      constraints: ["No paid ads"],
      requirements: ["GDPR compliant"],
    };

    const res = await api.createPlan("comp-1", payload);
    expect(res.id).toBe("plan-1");
    expect(res.status).toBe("proposed");
    expect(res.plan_steps).toHaveLength(1);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/ceo/plan",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify(payload),
      })
    );
  });

  it("getPlans returns array of plan summaries", async () => {
    const mockSummaries = [
      {
        id: "plan-1",
        company_id: "comp-1",
        user_id: "user-1",
        ceo_agent_id: "ceo-1",
        goal: "Expand to Europe",
        requested_outcome: null,
        priority: "high",
        status: "proposed",
        reasoning_summary: "Decomposition summary",
        step_count: 4,
        created_at: "2026-09-21T00:00:00Z",
        updated_at: "2026-09-21T00:00:00Z",
      },
    ];

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockSummaries,
    } as Response);

    const res = await api.getPlans("comp-1");
    expect(res).toHaveLength(1);
    expect(res[0].goal).toBe("Expand to Europe");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/ceo/plans",
      expect.objectContaining({
        method: "GET",
        credentials: "include",
      })
    );
  });

  it("getPlan returns single plan detail", async () => {
    const mockDetail = {
      id: "plan-1",
      company_id: "comp-1",
      user_id: "user-1",
      ceo_agent_id: "ceo-1",
      goal: "Expand to Europe",
      requested_outcome: null,
      priority: "high",
      status: "proposed",
      reasoning_summary: "Decomposition summary",
      context_snapshot: {},
      plan_steps: [],
      delegation_proposals: [],
      approval_requirements: [],
      risks: [],
      assumptions: [],
      created_at: "2026-09-21T00:00:00Z",
      updated_at: "2026-09-21T00:00:00Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockDetail,
    } as Response);

    const res = await api.getPlan("comp-1", "plan-1");
    expect(res.id).toBe("plan-1");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/ceo/plans/plan-1",
      expect.objectContaining({
        method: "GET",
        credentials: "include",
      })
    );
  });
  it("getProjects and createProject perform correct requests", async () => {
    const mockList = {
      items: [
        {
          id: "proj-1",
          company_id: "comp-1",
          name: "Project Titan",
          description: "Major milestone",
          objective: "Ship on time",
          status: "PLANNED",
          priority: "high",
          owner_user_id: "user-1",
          owner_agent_id: null,
          created_at: "2026-09-21T00:00:00Z",
          updated_at: "2026-09-21T00:00:00Z",
          completed_at: null,
          stats: {
            total_tasks: 5,
            completed_tasks: 2,
            blocked_tasks: 0,
            in_progress_tasks: 1,
            planned_tasks: 2,
          },
        },
      ],
      total: 1,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockList,
    } as Response);

    const res = await api.getProjects("comp-1", { status: "PLANNED" });
    expect(res.total).toBe(1);
    expect(res.items[0].name).toBe("Project Titan");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/projects?status=PLANNED",
      expect.objectContaining({ method: "GET" })
    );

    // Test createProject
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockList.items[0],
    } as Response);

    const created = await api.createProject("comp-1", { name: "Project Titan" });
    expect(created.name).toBe("Project Titan");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/projects",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("getTasks and createTask perform correct requests", async () => {
    const mockTask = {
      id: "task-1",
      company_id: "comp-1",
      project_id: "proj-1",
      parent_task_id: null,
      title: "Write Architecture Spec",
      description: "Draft specification",
      objective: "Approved RFC",
      created_by_user_id: "user-1",
      assigned_to_agent_id: "agent-1",
      assigned_to_user_id: null,
      department_id: "dept-1",
      status: "ASSIGNED",
      priority: "high",
      deadline: null,
      output: null,
      error_details: null,
      created_at: "2026-09-21T00:00:00Z",
      started_at: null,
      completed_at: null,
      dependencies: [],
      subtasks_count: 0,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ items: [mockTask], total: 1 }),
    } as Response);

    const res = await api.getTasks("comp-1", { project_id: "proj-1" });
    expect(res.total).toBe(1);
    expect(res.items[0].title).toBe("Write Architecture Spec");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/tasks?project_id=proj-1",
      expect.objectContaining({ method: "GET" })
    );

    // Test updateTaskStatus
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ...mockTask, status: "IN_PROGRESS" }),
    } as Response);

    const updated = await api.updateTaskStatus("comp-1", "task-1", { status: "IN_PROGRESS" });
    expect(updated.status).toBe("IN_PROGRESS");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/tasks/task-1/status",
      expect.objectContaining({ method: "PATCH" })
    );
  });

  it("delegateTask, getTaskDelegations, and listCompanyDelegations perform correct requests", async () => {
    const mockRecord = {
      id: "del-1",
      company_id: "comp-1",
      task_id: "task-1",
      delegated_by_user_id: "user-1",
      delegated_by_agent_id: null,
      delegated_to_agent_id: "agent-2",
      delegated_by_user_name: "Human Operator",
      delegated_to_agent_name: "Lead Frontend Engineer",
      delegated_to_agent_role: "frontend_engineer",
      delegated_by_agent_name: null,
      scope: null,
      depth: 1,
      reason: "Hand off UI work",
      status: "ASSIGNED",
      created_at: "2026-09-21T00:00:00Z",
    };

    // Test delegateTask
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockRecord,
    } as Response);

    const delegated = await api.delegateTask("comp-1", "task-1", {
      target_agent_id: "agent-2",
      reason: "Hand off UI work",
    });
    expect(delegated.id).toBe("del-1");
    expect(delegated.depth).toBe(1);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/tasks/task-1/delegate",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ target_agent_id: "agent-2", reason: "Hand off UI work" }),
      })
    );

    // Test getTaskDelegations
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [mockRecord],
    } as Response);

    const taskDels = await api.getTaskDelegations("comp-1", "task-1");
    expect(taskDels).toHaveLength(1);
    expect(taskDels[0].delegated_to_agent_name).toBe("Lead Frontend Engineer");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/tasks/task-1/delegations",
      expect.objectContaining({ method: "GET" })
    );

    // Test listCompanyDelegations
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ items: [mockRecord], total: 1 }),
    } as Response);

    const companyDels = await api.listCompanyDelegations("comp-1", { limit: 10 });
    expect(companyDels.total).toBe(1);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/delegations?limit=10",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("delegatePlan performs correct POST request to CEO delegation endpoint", async () => {
    const mockResult = {
      project_id: "proj-1",
      parent_task_id: "task-parent",
      child_task_ids: ["task-c1", "task-c2"],
      delegation_ids: ["del-1", "del-2"],
      plan_id: "plan-1",
      message: "Plan successfully decomposed and delegated.",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockResult,
    } as Response);

    const res = await api.delegatePlan("comp-1", "plan-1", { reason: "Execute strategic plan" });
    expect(res.project_id).toBe("proj-1");
    expect(res.child_task_ids).toHaveLength(2);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/ceo/plans/plan-1/delegate",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ reason: "Execute strategic plan" }),
      })
    );
  });

  it("executeTask performs POST request to execute endpoint", async () => {
    const mockExecution = {
      id: "exec-123",
      company_id: "comp-1",
      task_id: "task-1",
      agent_id: "agent-1",
      executed_by_user_id: "user-1",
      status: "SUCCESS",
      step_count: 4,
      duration_ms: 250,
      tokens_used: 1200,
      estimated_cost: 0.0024,
      result_summary: "Task executed successfully",
      deliverable: "export function Test() {}",
      steps_json: [
        {
          step_number: 1,
          thought: "Analyze requirements",
          action: "analyze",
          action_input: {},
          observation: "Complete",
          duration_ms: 50,
          tokens_used: 300,
        },
      ],
      error_details: null,
      created_at: "2026-09-21T00:00:00Z",
      completed_at: "2026-09-21T00:00:01Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockExecution,
    } as Response);

    const res = await api.executeTask("comp-1", "task-1", { max_steps: 5, max_duration_seconds: 60 });
    expect(res.id).toBe("exec-123");
    expect(res.status).toBe("SUCCESS");
    expect(res.step_count).toBe(4);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/tasks/task-1/execute",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ max_steps: 5, max_duration_seconds: 60 }),
      })
    );
  });

  it("getTaskExecutions fetches execution runs list", async () => {
    const mockList = {
      total: 1,
      items: [
        {
          id: "exec-123",
          company_id: "comp-1",
          task_id: "task-1",
          agent_id: "agent-1",
          executed_by_user_id: "user-1",
          status: "SUCCESS",
          step_count: 4,
          duration_ms: 250,
          tokens_used: 1200,
          estimated_cost: 0.0024,
          result_summary: "Task executed successfully",
          deliverable: "Deliverable text",
          steps_json: [],
          error_details: null,
          created_at: "2026-09-21T00:00:00Z",
          completed_at: "2026-09-21T00:00:01Z",
        },
      ],
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockList,
    } as Response);

    const res = await api.getTaskExecutions("comp-1", "task-1");
    expect(res.total).toBe(1);
    expect(res.items[0].id).toBe("exec-123");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/tasks/task-1/executions",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("getTools returns tool definitions", async () => {
    const mockTools = {
      total: 3,
      items: [
        {
          name: "web_search",
          provider: "search_adapter",
          description: "Search web",
          version: "1.0.0",
          risk_level: "LOW",
          requires_approval: false,
          allowed_roles: ["*"],
          input_schema: {},
          output_schema: {},
        },
      ],
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockTools,
    } as Response);

    const res = await api.getTools("comp-1", "software_engineer");
    expect(res.total).toBe(3);
    expect(res.items[0].name).toBe("web_search");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/tools?role=software_engineer",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("executeTool sends tool invocation payload and returns record", async () => {
    const mockRecord = {
      id: "tool-exec-123",
      company_id: "comp-1",
      agent_id: "agent-1",
      tool_name: "web_search",
      action: "search",
      risk_level: "LOW",
      requires_approval: false,
      status: "SUCCESS",
      input_params: { query: "test query" },
      output_data: { results: [] },
      duration_ms: 120,
      created_at: "2026-09-21T00:00:00Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockRecord,
    } as Response);

    const res = await api.executeTool("comp-1", {
      agent_id: "agent-1",
      tool_name: "web_search",
      action: "search",
      parameters: { query: "test query" },
    });

    expect(res.id).toBe("tool-exec-123");
    expect(res.status).toBe("SUCCESS");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/tools/execute",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          agent_id: "agent-1",
          tool_name: "web_search",
          action: "search",
          parameters: { query: "test query" },
        }),
      })
    );
  });

  it("getToolExecutions returns audit records", async () => {
    const mockExecs = {
      total: 1,
      items: [
        {
          id: "tool-exec-123",
          company_id: "comp-1",
          agent_id: "agent-1",
          tool_name: "documents",
          action: "read",
          risk_level: "LOW",
          requires_approval: false,
          status: "SUCCESS",
          input_params: {},
          output_data: {},
          duration_ms: 50,
          created_at: "2026-09-21T00:00:00Z",
        },
      ],
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockExecs,
    } as Response);

    const res = await api.getToolExecutions("comp-1", { toolName: "documents", status: "SUCCESS" });
    expect(res.total).toBe(1);
    expect(res.items[0].tool_name).toBe("documents");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/tools/executions?tool_name=documents&status=SUCCESS",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("getApprovals returns approval requests list", async () => {
    const mockApprovals = {
      total: 1,
      items: [
        {
          id: "appr-123",
          company_id: "comp-1",
          action_type: "DEPLOY_PRODUCTION",
          description: "Deploy release v2",
          payload: {},
          risk_level: "CRITICAL",
          status: "PENDING",
          created_at: "2026-09-22T00:00:00Z",
          updated_at: "2026-09-22T00:00:00Z",
        },
      ],
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockApprovals,
    } as Response);

    const res = await api.getApprovals("comp-1", { status: "PENDING", risk_level: "CRITICAL" });
    expect(res.total).toBe(1);
    expect(res.items[0].action_type).toBe("DEPLOY_PRODUCTION");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/approvals?status=PENDING&risk_level=CRITICAL",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("approveRequest sends POST with decision payload", async () => {
    const mockApproved = {
      id: "appr-123",
      company_id: "comp-1",
      action_type: "DEPLOY_PRODUCTION",
      description: "Deploy release v2",
      payload: {},
      risk_level: "CRITICAL",
      status: "APPROVED",
      decision_reason: "Signed off by security",
      created_at: "2026-09-22T00:00:00Z",
      updated_at: "2026-09-22T00:00:00Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockApproved,
    } as Response);

    const res = await api.approveRequest("comp-1", "appr-123", { decision_reason: "Signed off by security" });
    expect(res.status).toBe("APPROVED");
    expect(res.decision_reason).toBe("Signed off by security");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/approvals/appr-123/approve",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ decision_reason: "Signed off by security" }),
      })
    );
  });

  it("rejectRequest sends POST with decision payload", async () => {
    const mockRejected = {
      id: "appr-123",
      company_id: "comp-1",
      action_type: "DEPLOY_PRODUCTION",
      description: "Deploy release v2",
      payload: {},
      risk_level: "CRITICAL",
      status: "REJECTED",
      decision_reason: "Security vulnerability detected",
      created_at: "2026-09-22T00:00:00Z",
      updated_at: "2026-09-22T00:00:00Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockRejected,
    } as Response);

    const res = await api.rejectRequest("comp-1", "appr-123", { decision_reason: "Security vulnerability detected" });
    expect(res.status).toBe("REJECTED");
    expect(res.decision_reason).toBe("Security vulnerability detected");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/approvals/appr-123/reject",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ decision_reason: "Security vulnerability detected" }),
      })
    );
  });

  it("getCompanyState sends GET to memory state endpoint", async () => {
    const mockState = {
      company: { id: "comp-1", name: "Apex Corp" },
      departments: [],
      agents: [],
      projects: [],
      tasks_summary: { total: 0, by_status: {}, recent_active_tasks: [] },
      recent_approvals: [],
      decisions: [],
      generated_at: "2026-09-23T00:00:00Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockState,
    } as Response);

    const res = await api.getCompanyState("comp-1");
    expect(res.company.name).toBe("Apex Corp");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/memory/state",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("getCompanyDecisions sends GET with optional status filter", async () => {
    const mockDecisions = {
      items: [
        {
          id: "dec-1",
          company_id: "comp-1",
          title: "PostgreSQL Authority",
          decision: "Store state in PG",
          rationale: "ACID",
          evidence: {},
          status: "ACTIVE",
          created_at: "2026-09-23T00:00:00Z",
          updated_at: "2026-09-23T00:00:00Z",
        },
      ],
      total: 1,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockDecisions,
    } as Response);

    const res = await api.getCompanyDecisions("comp-1", "ACTIVE");
    expect(res.total).toBe(1);
    expect(res.items[0].title).toBe("PostgreSQL Authority");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/memory/decisions?status=ACTIVE",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("createCompanyDecision sends POST with decision payload", async () => {
    const mockCreated = {
      id: "dec-new",
      company_id: "comp-1",
      title: "Immutable Chains",
      decision: "Never mutate records",
      rationale: "Auditability",
      evidence: {},
      status: "ACTIVE",
      created_at: "2026-09-23T00:00:00Z",
      updated_at: "2026-09-23T00:00:00Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockCreated,
    } as Response);

    const res = await api.createCompanyDecision("comp-1", {
      title: "Immutable Chains",
      decision: "Never mutate records",
      rationale: "Auditability",
    });
    expect(res.id).toBe("dec-new");
    expect(res.status).toBe("ACTIVE");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/memory/decisions",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          title: "Immutable Chains",
          decision: "Never mutate records",
          rationale: "Auditability",
        }),
      })
    );
  });

  it("supersedeCompanyDecision sends POST to supersede endpoint", async () => {
    const mockSuperseded = {
      id: "dec-v2",
      company_id: "comp-1",
      title: "Immutable Chains V2",
      decision: "Enhanced chain",
      rationale: "Better scaling",
      evidence: {},
      status: "ACTIVE",
      created_at: "2026-09-23T00:00:00Z",
      updated_at: "2026-09-23T00:00:00Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockSuperseded,
    } as Response);

    const res = await api.supersedeCompanyDecision("comp-1", "dec-v1", {
      title: "Immutable Chains V2",
      decision: "Enhanced chain",
      rationale: "Better scaling",
    });
    expect(res.id).toBe("dec-v2");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/memory/decisions/dec-v1/supersede",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("inquireCeo sends POST with question payload", async () => {
    const mockInquiryRes = {
      answer: "The company is Apex Corp.",
      citations: [{ source_type: "COMPANY", source_id: "comp-1", reference: "Company: Apex Corp" }],
      grounded_state_timestamp: "2026-09-23T00:00:00Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockInquiryRes,
    } as Response);

    const res = await api.inquireCeo("comp-1", "What is our company name?");
    expect(res.answer).toBe("The company is Apex Corp.");
    expect(res.citations).toHaveLength(1);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/ceo/inquire",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ question: "What is our company name?" }),
      })
    );
  });


  it("getProjectBoard sends GET to project board endpoint and returns board data", async () => {
    const mockBoard = {
      project: { id: "proj-1", name: "Board Alpha", status: "ACTIVE" },
      columns: [
        { id: "READY", title: "Ready", statuses: ["READY"], color: "blue", task_count: 1 },
        { id: "IN_PROGRESS", title: "In Progress", statuses: ["IN_PROGRESS"], color: "amber", task_count: 1 },
      ],
      tasks: [
        { id: "task-1", title: "Task One", status: "READY", priority: "high" },
        { id: "task-2", title: "Task Two", status: "IN_PROGRESS", priority: "critical" },
      ],
      allowed_transitions: {
        READY: ["IN_PROGRESS", "BLOCKED"],
        IN_PROGRESS: ["VERIFYING", "COMPLETED"],
      },
      summary: {
        total_tasks: 2,
        completed_tasks: 0,
        in_progress_tasks: 1,
        waiting_tasks: 0,
        blocked_tasks: 0,
        completion_rate: 0.0,
      },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockBoard,
    } as Response);

    const res = await api.getProjectBoard("comp-1", "proj-1");
    expect(res.project.name).toBe("Board Alpha");
    expect(res.columns).toHaveLength(2);
    expect(res.tasks).toHaveLength(2);
    expect(res.summary.total_tasks).toBe(2);
    expect(res.allowed_transitions["READY"]).toContain("IN_PROGRESS");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/projects/proj-1/board",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("getActivity returns paginated company activity events", async () => {
    const mockActivity = {
      items: [
        {
          id: "act-1",
          company_id: "comp-1",
          project_id: "proj-1",
          task_id: "task-1",
          actor_type: "user",
          actor_id: "user-1",
          event_type: "TASK_CREATED",
          message: "Created task 'Build Auth'",
          metadata: { priority: "high" },
          created_at: "2026-09-23T05:00:00Z",
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockActivity,
    } as Response);

    const res = await api.getActivity("comp-1", { search: "Auth", limit: 10 });
    expect(res.total).toBe(1);
    expect(res.items).toHaveLength(1);
    expect(res.items[0].event_type).toBe("TASK_CREATED");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/activity?search=Auth&limit=10",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("getProjectActivity returns project-scoped activity events", async () => {
    const mockActivity = {
      items: [
        {
          id: "act-2",
          company_id: "comp-1",
          project_id: "proj-1",
          task_id: null,
          actor_type: "user",
          actor_id: "user-1",
          event_type: "PROJECT_CREATED",
          message: "Created project 'Alpha'",
          metadata: {},
          created_at: "2026-09-23T05:00:00Z",
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockActivity,
    } as Response);

    const res = await api.getProjectActivity("comp-1", "proj-1");
    expect(res.total).toBe(1);
    expect(res.items[0].project_id).toBe("proj-1");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/projects/proj-1/activity",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("getCompanyPresence returns list of agent presences", async () => {
    const mockPresences = {
      items: [
        {
          id: "pres-1",
          agent_id: "agent-1",
          agent_name: "CEO",
          agent_role: "Executive",
          company_id: "comp-1",
          status: "WORKING",
          current_task_id: "task-1",
          current_activity: "Planning goals",
          last_heartbeat_at: "2026-09-23T20:00:00Z",
          started_at: "2026-09-23T19:50:00Z",
          updated_at: "2026-09-23T20:00:00Z",
          duration_seconds: 600,
          is_stale: false,
          details: {},
        },
      ],
      total: 1,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockPresences,
    } as Response);

    const res = await api.getCompanyPresence("comp-1");
    expect(res.total).toBe(1);
    expect(res.items[0].status).toBe("WORKING");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/presence",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("getPresenceSummary returns aggregated presence counts", async () => {
    const mockSummary = {
      total_agents: 3,
      working_count: 1,
      idle_count: 2,
      waiting_count: 0,
      blocked_count: 0,
      error_count: 0,
      offline_count: 0,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockSummary,
    } as Response);

    const res = await api.getPresenceSummary("comp-1");
    expect(res.working_count).toBe(1);
    expect(res.idle_count).toBe(2);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/presence/summary",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("sendAgentHeartbeat sends POST with check-in payload", async () => {
    const mockPresence = {
      id: "pres-1",
      agent_id: "agent-1",
      company_id: "comp-1",
      status: "WORKING",
      current_step: "Running search",
      last_heartbeat_at: "2026-09-23T20:00:00Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockPresence,
    } as Response);

    const res = await api.sendAgentHeartbeat("comp-1", "agent-1", {
      current_step: "Running search",
    });
    expect(res.current_step).toBe("Running search");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/agents/agent-1/presence/heartbeat",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ current_step: "Running search" }),
      })
    );
  });

  it("getCompanyErrors and getCompanyErrorSummary perform correct requests", async () => {
    const mockErrors = {
      items: [
        {
          id: "err-1",
          company_id: "comp-1",
          title: "Unhandled NPE",
          severity: "HIGH",
          status: "OPEN",
          detected_by: "agent:Coder",
          created_at: "2026-09-24T12:00:00Z",
          evidence: {},
        },
      ],
      total: 1,
      open_count: 1,
      investigating_count: 0,
      resolved_count: 0,
      verified_count: 0,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockErrors,
    } as Response);

    const res = await api.getCompanyErrors("comp-1", { status: "OPEN" });
    expect(res.total).toBe(1);
    expect(res.items[0].title).toBe("Unhandled NPE");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/errors?status=OPEN",
      expect.objectContaining({ method: "GET" })
    );

    const mockSummary = {
      total_errors: 5,
      open_count: 2,
      critical_count: 1,
      resolved_count: 2,
    };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockSummary,
    } as Response);

    const summary = await api.getCompanyErrorSummary("comp-1");
    expect(summary.total_errors).toBe(5);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/errors/summary",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("createError, assignError, resolveError, verifyError perform correct mutations", async () => {
    const mockError = {
      id: "err-1",
      company_id: "comp-1",
      title: "Broken route",
      severity: "CRITICAL",
      status: "OPEN",
      detected_by: "QA Tester",
      created_at: "2026-09-24T12:00:00Z",
      evidence: {},
    };

    // 1. Create
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockError,
    } as Response);

    const created = await api.createError("comp-1", {
      title: "Broken route",
      detected_by: "QA Tester",
      severity: "CRITICAL",
    });
    expect(created.id).toBe("err-1");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/errors",
      expect.objectContaining({ method: "POST" })
    );

    // 2. Assign
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ...mockError, status: "ASSIGNED", assigned_to: "Lead Dev" }),
    } as Response);

    const assigned = await api.assignError("comp-1", "err-1", { assigned_to: "Lead Dev" });
    expect(assigned.status).toBe("ASSIGNED");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/errors/err-1/assign",
      expect.objectContaining({ method: "POST" })
    );

    // 3. Resolve
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ...mockError, status: "RESOLVED", resolution: "Fixed logic" }),
    } as Response);

    const resolved = await api.resolveError("comp-1", "err-1", {
      resolved_by: "Lead Dev",
      resolution: "Fixed logic",
    });
    expect(resolved.status).toBe("RESOLVED");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/errors/err-1/resolve",
      expect.objectContaining({ method: "POST" })
    );

    // 4. Verify
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ...mockError, status: "VERIFIED", verified_by: "Auditor" }),
    } as Response);

    const verified = await api.verifyError("comp-1", "err-1", {
      verified_by: "Auditor",
      evidence: { passed: true },
    });
    expect(verified.status).toBe("VERIFIED");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/errors/err-1/verify",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("getTaskEngineeringView fetches engineering context and file changes", async () => {
    const mockView = {
      task_id: "task-1",
      company_id: "comp-1",
      context: {
        id: "ctx-1",
        company_id: "comp-1",
        task_id: "task-1",
        repository: "moon90/AICompanyOS",
        branch: "feat/engineering-file-tracking",
        pull_request_number: "42",
        pull_request_url: "https://github.com/moon90/AICompanyOS/pull/42",
        pull_request_title: "feat: Phase 16 tracking",
        commit_count: 3,
        test_status: "PASSED",
        test_output_summary: "All 187 tests passed",
        verification_state: "VERIFIED",
        verification_notes: "Reviewed and approved",
        created_at: "2026-09-24T20:00:00Z",
        updated_at: "2026-09-24T20:05:00Z",
      },
      file_changes: [
        {
          id: "fc-1",
          company_id: "comp-1",
          task_id: "task-1",
          file_path: "apps/web/app/tasks/page.tsx",
          repository: "moon90/AICompanyOS",
          branch: "feat/engineering-file-tracking",
          agent_name: "Frontend Agent",
          change_type: "MODIFIED",
          commit_hash: "abcd123",
          additions: 45,
          deletions: 5,
          last_modified_at: "2026-09-24T20:00:00Z",
          created_at: "2026-09-24T20:00:00Z",
        },
      ],
      total_files_changed: 1,
      total_additions: 45,
      total_deletions: 5,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockView,
    } as Response);

    const view = await api.getTaskEngineeringView("comp-1", "task-1");
    expect(view.task_id).toBe("task-1");
    expect(view.context?.branch).toBe("feat/engineering-file-tracking");
    expect(view.total_files_changed).toBe(1);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/engineering/tasks/task-1",
      expect.objectContaining({ credentials: "include" })
    );
  });

  it("upsertEngineeringContext updates task context and verification state", async () => {
    const mockContext = {
      id: "ctx-1",
      company_id: "comp-1",
      task_id: "task-1",
      repository: "moon90/AICompanyOS",
      branch: "feat/engineering-file-tracking",
      commit_count: 4,
      test_status: "PASSED",
      verification_state: "VERIFIED",
      verification_notes: "QA Verified",
      created_at: "2026-09-24T20:00:00Z",
      updated_at: "2026-09-24T20:10:00Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockContext,
    } as Response);

    const res = await api.upsertEngineeringContext("comp-1", "task-1", {
      verification_state: "VERIFIED",
      verification_notes: "QA Verified",
    });
    expect(res.verification_state).toBe("VERIFIED");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/engineering/tasks/task-1/context",
      expect.objectContaining({ method: "PUT" })
    );
  });

  it("recordTaskFileChanges batches file additions and commits", async () => {
    const mockFiles = [
      {
        id: "fc-1",
        company_id: "comp-1",
        task_id: "task-1",
        file_path: "apps/web/lib/api.ts",
        repository: "moon90/AICompanyOS",
        branch: "main",
        agent_name: "Lead Engineer",
        change_type: "MODIFIED",
        additions: 30,
        deletions: 2,
        last_modified_at: "2026-09-24T20:00:00Z",
        created_at: "2026-09-24T20:00:00Z",
      },
    ];

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockFiles,
    } as Response);

    const res = await api.recordTaskFileChanges("comp-1", "task-1", [
      {
        file_path: "apps/web/lib/api.ts",
        additions: 30,
        deletions: 2,
      },
    ]);
    expect(res).toHaveLength(1);
    expect(res[0].file_path).toBe("apps/web/lib/api.ts");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/engineering/tasks/task-1/files",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("getCompanyFileHistory retrieves aggregated file touches", async () => {
    const mockHistory = [
      {
        file_path: "apps/web/lib/api.ts",
        repository: "moon90/AICompanyOS",
        branches: ["main", "feat/tracking"],
        change_count: 5,
        last_modified_at: "2026-09-24T20:00:00Z",
      },
    ];

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockHistory,
    } as Response);

    const res = await api.getCompanyFileHistory("comp-1", "main", 10);
    expect(res).toEqual(mockHistory);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/companies/comp-1/engineering/files?branch=main&limit=10",
      expect.objectContaining({ credentials: "include" })
    );
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

