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

