# AI Company OS — Implementation Status

## Current Phase
**Phase 10 — Approval & Oversight System** (COMPLETE)

---

## Completed Work

### Phase 0 — Project Foundation (COMPLETE)
* Initialized Git version control on branch `main`.
* Established root configuration files: `.gitignore`, `.editorconfig`, `pyproject.toml`, `README.md`.
* Configured local development infrastructure via `docker-compose.yml` (PostgreSQL 16 with pgvector, Redis 7).
* Created modular monolith directory layout:
  * `apps/api/`, `apps/web/`
  * `agents/`, `orchestration/`, `domain/`, `application/`, `infrastructure/`, `tools/`, `policies/`, `memory/`, `database/`, `tests/`
* Built minimal FastAPI application with deterministic `GET /health` endpoint decoupled through `HealthService`.
* Established SQLAlchemy 2.0 and Alembic migration foundation with initial baseline migration (`0001_initial_baseline.py`).
* Built minimal Next.js 14 frontend application shell with Executive dark theme tokens per `docs/UI.md`.
* Configured developer toolchain: `pytest`, `ruff`, `mypy` (strict), `eslint`, and GitHub Actions CI workflow.

### Phase 1 — Authentication (COMPLETE)
* **Domain Layer:**
  * Defined domain-level exceptions in `domain/users/exceptions.py` (`UserAlreadyExistsError`, `InvalidCredentialsError`, `UserInactiveError`, `SessionExpiredError`, `SessionNotFoundError`, `RateLimitExceededError`, `PasswordValidationError`).
* **Security & Infrastructure:**
  * Implemented bcrypt password hashing and verification in `infrastructure/security/password.py`.
  * Implemented cryptographically secure token generation and SHA-256 hashing in `infrastructure/security/tokens.py`.
  * Implemented sliding-window brute-force rate limiter in `infrastructure/security/rate_limiter.py`.
  * Updated configuration in `infrastructure/config.py` with session expiration and cookie settings.
* **Authoritative Persistence:**
  * Defined `User` and `UserSession` SQLAlchemy models in `infrastructure/database/models.py`.
  * Generated and applied Alembic migration `0002_create_users_and_sessions.py` with verified zero schema drift.
* **Application Services:**
  * Implemented `AuthService` in `application/services/auth_service.py` orchestrating registration, credential verification, rate limit enforcement, session creation, session validation, and session revocation.
* **API Layer:**
  * Created Pydantic request and response schemas in `apps/api/schemas/auth.py`.
  * Created authentication dependency `get_current_user` in `apps/api/dependencies/auth.py` supporting both HttpOnly cookies and `Authorization: Bearer <token>` headers.
  * Implemented thin route handlers in `apps/api/routes/auth.py`:
    * `POST /api/v1/auth/register` (201 Created)
    * `POST /api/v1/auth/login` (200 OK, sets secure HttpOnly cookie)
    * `POST /api/v1/auth/logout` (200 OK, revokes session from PostgreSQL, clears cookie)
    * `GET /api/v1/auth/me` (200 OK, returns authenticated user profile)
* **Frontend UI & Route Protection:**
  * Created typed API client in `apps/web/lib/api.ts` with automatic cookie pass-through.
  * Built executive `/login` page in `apps/web/app/login/page.tsx` with logo, email, password, forgot password prompt, and error alert displays.
  * Built executive `/register` page in `apps/web/app/register/page.tsx` with full name, email, password, confirm password, and client-side validation.
  * Implemented route protection in `apps/web/middleware.ts` redirecting unauthenticated users to `/login`.

### Phase 2 — Application Shell & Dashboard (COMPLETE)
* **Design System & Semantic Tokens (`docs/UI.md` § 4, 6, 7, 8):**
  * Extended `apps/web/tailwind.config.ts` and `apps/web/app/globals.css` with semantic color hierarchy (`surface`, `surface-elevated`, `surface-strong`, `border`, `border-strong`, `text-primary`, `text-secondary`, `text-muted`, `primary`, `success`, `warning`, `error`, `info`).
  * Enforced Executive dark theme priority with light theme variable parity.
  * Configured typographic scale (Inter font family, monospace font for technical identifiers).
* **Application Shell Architecture (`apps/web/components/shell/`):**
  * Built `Sidebar.tsx` supporting desktop fixed layout and responsive mobile drawer navigation with all 9 Phase 2 sections from `docs/Phases.md` § 6:
    * `Dashboard` (`/`) [Active Executive Overview]
    * `Company` (`/company`) [Phase 3 roadmap badge]
    * `CEO Orchestrator` (`/ceo`) [Phase 5 roadmap badge]
    * `Agent Registry` (`/agents`) [Phase 4 roadmap badge]
    * `Projects` (`/projects`) [Phase 6 roadmap badge]
    * `Tasks` (`/tasks`) [Phase 6 roadmap badge]
    * `Approvals` (`/approvals`) [Phase 7 roadmap badge]
    * `Activity` (`/activity`) [Phase 10 roadmap badge]
    * `Settings` (`/settings`) [Phase 0 foundational settings]
  * Built `TopBar.tsx` featuring real system operational telemetry badge (`Operational · Phase 4 Active`), company indicator, and authenticated user profile menu with logout flow.
  * Built `Shell.tsx` responsive layout coordinator with mobile hamburger toggle and content wrapping.
* **Executive Dashboard (`apps/web/app/page.tsx`):**
  * Implemented Recent Activity Panel with honest empty state:
    * Icon, title, and descriptive text explaining real-time event streaming activates in Phase 13.
  * Implemented System Foundation & Infrastructure Telemetry Panel:
    * Displays live telemetry directly from backend `/api/v1/system/status` and `/api/v1/auth/me` (PostgreSQL connectivity verified via `SELECT 1`, authoritative session state, FastAPI gateway version, roadmap phase).
* **Dedicated Placeholder Pages:**
  * Implemented structured `PhaseBoundaryCard.tsx` component.
  * Added dedicated placeholder pages for all future navigation destinations (`/company`, `/ceo`, `/agents`, `/projects`, `/tasks`, `/approvals`, `/activity`, `/settings`), rendering inside `ShellLayout` with specification cross-references and zero simulated data.
* **Backend Telemetry Service & API:**
  * Implemented `SystemService` in `application/services/system_service.py` performing live database probe queries decoupled from route handlers.
  * Implemented `SystemStatusResponse` in `apps/api/schemas/system.py`.
  * Implemented protected route `GET /api/v1/system/status` in `apps/api/routes/system.py`.
  * Mounted `system_router` on FastAPI application in `apps/api/main.py`.
* **Repository Configuration:**
  * Corrected `.gitignore` rule from `lib/` to `/lib/` to ensure frontend library modules (`apps/web/lib/`) are tracked.
* **Testing & Quality Assurance:**
  * Added backend unit tests in `tests/unit/test_system_service.py` (success and simulated database failure).
  * Added backend integration tests in `tests/integration/test_api_system.py` (unauthenticated 401 and authenticated 200).
  * Configured Vitest in `apps/web/vitest.config.mts` with happy-dom environment.
  * Added frontend unit tests in `apps/web/lib/api.test.ts` and `apps/web/components/shell/shell.test.ts`.

### Phase 3 — Company & Organization (COMPLETE)
* **Authoritative Persistence & Models (`infrastructure/database/models.py`):**
  * `Company`: Primary entity with UUID pk, `name`, `description`, `mission`, `industry`, `status` (active/archived), `created_at`, `updated_at`.
  * `CompanyMember`: Explicit membership linking users to companies with `role` (`owner`, `admin`, `member`), `created_at`, `updated_at`, and `UniqueConstraint("company_id", "user_id")`. Avoids "user = company owner" conflation.
  * `Department`: Company-scoped organizational unit with UUID pk, `company_id`, `name`, `code`, `description`, `lead_role`, `status`, and `UniqueConstraint("company_id", "code")`.
  * Proper foreign key cascading (`CASCADE`), timestamps, and B-tree indexes (`ix_companies_status`, `ix_company_members_user_id`, `ix_departments_company_id`).
* **Database Migrations:**
  * Created and verified Alembic migration `0003_create_companies_and_org.py`.
  * Preserved existing migrations `0001` and `0002`.
  * Validated upgrade to head, downgrade, and re-upgrade with 0 schema drift (`alembic check`).
* **Domain Layer (`domain/company/exceptions.py`):**
  * Defined typed domain exceptions: `CompanyNotFoundError`, `CompanyAccessDeniedError`, `DepartmentNotFoundError`, `DepartmentAlreadyExistsError`, `InvalidCompanyDataError`.
* **Multi-Company Data Isolation & Application Services (`application/services/company_service.py`):**
  * Built `CompanyService` enforcing company isolation at the database query level (never relying on frontend filtering).
  * Auto-provisions the 5 foundational departments per `docs/Phases.md` § 7 upon company creation:
    * CTO (Technology & Engineering)
    * CMO (Marketing & Growth)
    * Sales (Sales & Revenue)
    * Finance (Finance & Accounting)
    * Operations (Business Operations & Legal)
  * Implemented methods: `create_company`, `get_user_companies`, `get_company`, `update_company`, `get_departments`, `create_department`, `update_department`, `get_company_members`.
  * Strictly verifies `CompanyMember.user_id == current_user.id` on every company-scoped operation.
* **API Layer (`apps/api/schemas/company.py`, `apps/api/routes/company.py`):**
  * Pydantic schemas validating inputs and providing explicit response contracts.
  * Thin route handlers mounted under `/api/v1/companies`:
    * `GET /api/v1/companies` (200 OK — list authenticated user's companies)
    * `POST /api/v1/companies` (201 Created — establish new company with default departments)
    * `GET /api/v1/companies/{company_id}` (200 OK — company profile)
    * `PATCH /api/v1/companies/{company_id}` (200 OK — update company profile, owner/admin only)
    * `GET /api/v1/companies/{company_id}/departments` (200 OK — list departments)
    * `POST /api/v1/companies/{company_id}/departments` (201 Created — create department)
    * `PATCH /api/v1/companies/{company_id}/departments/{department_id}` (200 OK — update department)
    * `GET /api/v1/companies/{company_id}/members` (200 OK — list members)
* **Frontend Company Management UI (`apps/web/app/company/page.tsx`):**
  * Replaced `PhaseBoundaryCard` placeholder with real authenticated company workspace.
  * Initial State: Clean creation wizard if no company exists.
  * Active State: Multi-tab executive console:
    * **Overview & Mission:** Company profile, industry, mission statement, status, core metadata.
    * **Departments:** Grid of all departments with codes, names, leadership roles, and "Add Department" drawer modal.
    * **Organizational Structure:** Visual hierarchy (`Founder/Executive Leadership -> Phase 5 CEO Orchestrator -> Phase 4 Department Heads`). No fake agents or runtime entities.
    * **Members & Governance:** Real member roster from PostgreSQL with role badges and company isolation boundaries.
    * **Settings:** Edit company name, mission, description, and industry with live updates.
* **Dashboard Integration (`apps/web/app/page.tsx`):**
  * Real-time executive header reflects the authenticated user's active company name, industry, and mission.
  * System telemetry panel displays "Organization State" with authoritative company name and active department count.
  * If unprovisioned, displays an executive prompt directing the user to `/company`.
  * Maintained honest metric cards (0 active agents, 0 projects, 0 tasks) with zero simulated operational numbers.
* **Frontend Client & Testing:**
  * Added company, department, and member methods to `apps/web/lib/api.ts`.
  * Added frontend unit tests for all company endpoints in `apps/web/lib/api.test.ts`.
* **Testing & Quality Assurance:**
  * Added 7 unit tests in `tests/unit/test_company_service.py` covering isolation, creation, duplicates, updates, and validations.
  * Added comprehensive lifecycle & multi-company isolation integration test in `tests/integration/test_api_company.py`.
  * Verified 22/22 backend tests passing, 8/8 frontend tests passing, 100% type safety in strict mode.

### Phase 4 — Agent Registry (COMPLETE)
* **Domain Layer:**
  * Defined agent domain exceptions in `domain/agents/exceptions.py` (`AgentNotFoundError`, `AgentAccessDeniedError`, `InvalidAgentHierarchyError`, `InvalidAgentDepartmentError`, `DuplicateAgentVersionError`, `InvalidAgentDataError`).
* **Authoritative Persistence:**
  * Defined `Agent` model in `infrastructure/database/models.py`:
    * Fields: `id`, `company_id`, `department_id`, `name`, `role`, `type` (`executive`, `manager`, `specialist`, `worker`), `reports_to` (self-referencing foreign key), `mission`, `status` (`active`, `inactive`, `archived`), `authority_level` (1–5), `created_at`, `updated_at`.
    * Foreign keys with indexes: `company_id` (cascade delete), `department_id` (restrict delete), `reports_to` (set null on delete).
    * Compound indexes for fast filtered lookups: `ix_agents_company_status`, `ix_agents_company_department`.
  * Defined `AgentDefinition` model in `infrastructure/database/models.py`:
    * Versioned snapshot preserving prompt and capability history per Rule 129 (`cmo@1.0`, `cmo@1.1`).
    * Fields: `id`, `agent_id`, `version`, `system_prompt`, `model`, `capabilities` (JSON), `tools` (JSON), `configuration` (JSON), `is_current` (boolean), `created_at`.
    * Unique constraint: `(agent_id, version)` ensuring no version overwriting.
    * Partial / composite index: `ix_agent_definitions_agent_current`.
  * Alembic Migration `database/migrations/versions/0004_create_agent_registry.py`:
    * Revision ID `0004_create_agent_registry` (26 chars, strictly compliant with PostgreSQL 32-char alembic limit).
    * Applied cleanly with reversible downgrade and re-upgrade testing.
    * Verified with `alembic check`: 0 schema drift detected.
* **Application Services (`application/services/agent_service.py`):**
  * `AgentService` strictly enforces multi-tenant boundary checks via `_verify_membership`.
  * Cross-company department validation: validates `department.company_id == agent.company_id`.
  * Cross-company manager validation: validates `manager.company_id == agent.company_id`.
  * Directed acyclic graph (DAG) cycle detection prevents self-cycles, 2-agent cycles, and multi-agent reporting loops.
  * `create_agent` automatically snapshots `AgentDefinition` version `1.0` with `is_current=True`.
  * `update_agent` updates organizational attributes and safely updates hierarchy references.
  * `create_agent_definition` creates new versions and automatically demotes previous current versions (`is_current=False`).
  * `provision_default_agents` automatically seeds the 11 foundational organization agents specified in `docs/Phases.md` § 8 (CEO, CTO, Software Architect, Full Stack Engineer, CMO, Marketing Strategist, Copywriter, Sales Director, Lead Researcher, Sales Analyst, Executive Assistant).
* **API Layer (`apps/api/routes/agent.py`):**
  * Thin route handlers mounted under `/api/v1/companies/{company_id}/agents`:
    * `GET /` — List agents with optional department, type, and status filtering.
    * `POST /` — Register new agent with initial definition.
    * `POST /provision-defaults` — Provision foundational 11 agents.
    * `GET /{agent_id}` — Get agent details including current definition and reporting line.
    * `PATCH /{agent_id}` — Update agent organizational attributes.
    * `GET /{agent_id}/definitions` — List definition version history.
    * `POST /{agent_id}/definitions` — Publish new versioned agent definition.
* **Frontend UI & Dashboard Integration:**
  * Replaced `PhaseBoundaryCard` at `/agents` with the authoritative Agent Registry Workspace:
    * Search & filter controls by department, agent type, and registry status.
    * Clear distinction between Registry Status (`active`, `inactive`, `archived`) and Runtime Presence (`0 runtime active`).
    * Agent cards displaying name, role, department, manager, model, version, authority level, and mission.
    * Interactive Agent Detail Drawer showing full hierarchy, declared capabilities, tools, system prompt, and version history.
    * "New Version" form directly inside drawer to evolve agent definitions per Rule 129.
    * "Register Agent" modal with complete validation and department selection.
    * "Provision Default Organization" action for 1-click foundational agent seeding.
  * Dashboard Integration (`apps/web/app/page.tsx`):
    * Real registered agent count displayed from PostgreSQL.
    * Active Agents card preserves honest `0` runtime presence with explicit note that the execution loop begins in Phase 5.
    * TopBar telemetry updated to `Phase 4 Active`.
* **Testing & Quality Assurance:**
  * Backend Unit Tests (`tests/unit/test_agent_service.py`): 7 comprehensive tests covering creation, validation, cross-company isolation, cycle prevention, versioning, and default provisioning.
  * Backend Integration Tests (`tests/integration/test_api_agent.py`): Complete end-to-end API lifecycle and cross-tenant isolation tests.
  * Frontend Tests (`apps/web/lib/api.test.ts`): Unit tests covering all agent API client functions.

### Phase 5 — CEO Orchestrator Foundation (COMPLETE)
* **Domain & Orchestration Layer:**
  * Defined CEO domain exceptions in `domain/ceo/exceptions.py` (`CeoNotFoundError`, `CeoAccessDeniedError`, `PlanNotFoundError`, `InvalidGoalError`, `InvalidPlanGraphError`, `PlanDepthExceededError`).
  * Defined strongly-typed Pydantic orchestration models in `orchestration/planner/schemas.py`:
    * `GoalIntake`: Structured goal input (`objective`, `requested_outcome`, `constraints`, `priority`, `requirements`).
    * `PlanStep`: Discrete task graph node (`step_id`, `title`, `description`, `assigned_agent_id`, `assigned_agent_role`, `department_code`, `depends_on`, `required_capabilities`, `expected_output`, `verification_criteria`).
    * `DelegationProposal`: Typed delegation proposal (`proposal_id`, `source_agent_id`, `target_agent_id`, `target_role`, `objective`, `scope`, `expected_output`, `required_capabilities`, `constraints`, `authority_level_required`).
    * `ApprovalRequirement`: Mandatory governance approval gate (`step_id`, `action_description`, `risk_level`, `reason_for_approval`).
    * `PlanResult`: Unified structured plan proposal with audit-safe reasoning summaries, DAG steps, delegation proposals, risks, and assumptions.
  * Built DAG validation engine in `orchestration/planner/dag_validator.py`:
    * Cycle detection via Kahn's algorithm (topological sort).
    * Self-dependency rejection (`step.step_id in step.depends_on`).
    * Missing dependency rejection (all references must resolve within plan).
    * Company agent validation (assigned agents must exist in company active registry).
    * Bounded safety limits enforcement (`MAX_PLAN_STEPS = 20`, `MAX_DEPENDENCY_DEPTH = 5`).
* **Provider-Agnostic LLM Gateway (`infrastructure/llm/`):**
  * `BaseLLMProvider`: Abstract provider contract for structured plan generation.
  * `DeterministicPlannerProvider`: Fast, 100% reproducible planning provider for deterministic decomposition, offline development, and CI/CD execution.
  * `LLMGateway`: Decouples application services from model providers and strictly validates provider output against DAG constraints before returning.
* **Authoritative Persistence (`infrastructure/database/models.py`):**
  * Defined `CeoPlan` model (`ceo_plans` table):
    * Columns: `id`, `company_id` (FK), `user_id` (FK), `ceo_agent_id` (FK nullable), `goal`, `requested_outcome`, `priority`, `status` (`proposed`, `under_review`, `rejected`, `superseded`), `reasoning_summary`, `context_snapshot`, `plan_steps`, `delegation_proposals`, `approval_requirements`, `risks`, `assumptions`, `created_at`, `updated_at`.
    * Indexes: `ix_ceo_plans_company_created`, `ix_ceo_plans_company_status`.
  * Alembic Migration `database/migrations/versions/0005_create_ceo_plans.py`:
    * Revision ID `0005_create_ceo_plans` (21 characters, <= 32-char limit).
    * Applied and verified with reversible downgrade/re-upgrade.
    * `alembic check`: 0 schema drift detected.
* **Application Services (`application/services/ceo_service.py`):**
  * `CeoService` orchestrates CEO operations with multi-tenant company isolation:
    * `get_company_ceo`: Resolves authoritative CEO agent record (`role="ceo"` or `"Chief Executive Officer"`).
    * `get_ceo_context`: Assembles live PostgreSQL state (company profile, departments, registered agents, declared capabilities, tools, active definition models).
    * `generate_plan`: Validates goal, gathers context, delegates to `LLMGateway`, verifies DAG constraints, and persists plan proposal with status `"proposed"`.
    * `list_plans`: Lists historical company plan proposals.
    * `get_plan`: Retrieves specific plan detail and DAG.
* **API Layer (`apps/api/routes/ceo.py`):**
  * Endpoints mounted at `/api/v1/companies/{company_id}/ceo`:
    * `GET /context` — Authoritative CEO company context and resolved identity (HTTP 200).
    * `POST /plan` — Submit goal, generate structured plan and DAG proposal (HTTP 201).
    * `GET /plans` — List historical company plans (HTTP 200).
    * `GET /plans/{plan_id}` — Retrieve full plan proposal details (HTTP 200).
* **Frontend UI & Dashboard Integration:**
  * Transformed `/ceo` placeholder into the authoritative **CEO Command Center** (`apps/web/app/ceo/page.tsx`):
    * CEO Identity banner displaying active CEO agent, Authority Level 5, and planning mode.
    * Missing CEO warning banner directing users to `/agents` if unprovisioned.
    * Strategic Goal Intake command box with objective, outcome, priority, and constraints.
    * Prominent proposal banner: `"PROPOSAL ONLY — This plan is an executive recommendation awaiting human governance approval."`
    * Visual Task Graph (DAG) viewer showing steps, dependencies, assigned roles, capabilities, and verification criteria.
    * Typed Delegation Proposals table.
    * Mandatory Governance Approval Gates & Risk Analysis matrix.
    * Plan Proposals History sidebar with instant inspection.
  * Dashboard Integration (`apps/web/app/page.tsx`):
    * TopBar updated to `Operational · Phase 5 Active`.
    * Active Operations panel displays live CEO planning status (`${planCount} strategic plan proposals synthesized`).
    * Active Agents metric maintained at honest `0` runtime active (`${agentCount} registered (0 runtime active)`).
    * Organization telemetry displays `${departmentCount} Depts · ${agentCount} Agents · ${planCount} Plans`.
* **Testing & Quality Assurance:**
  * Added 10 unit tests in `tests/unit/test_planner_dag.py` covering valid DAGs, self-dependencies, 2-node cycles, multi-node cycles, missing dependencies, foreign agent IDs, max steps, and max depth.
  * Added 7 unit tests in `tests/unit/test_ceo_service.py` covering CEO resolution, context assembly, plan generation, isolation, goal validation, and plan retrieval.
  * Added comprehensive lifecycle & isolation integration test in `tests/integration/test_api_ceo.py`.
  * Added 4 frontend client unit tests in `apps/web/lib/api.test.ts`.

### Phase 6 — Projects & Basic Tasks (COMPLETE)
* **Authoritative Persistence & Data Modeling (`infrastructure/database/models.py`):**
  * `Project` model (`projects` table) with fields: `id`, `company_id`, `name`, `description`, `objective`, `status` (`PLANNED`, `ACTIVE`, `BLOCKED`, `COMPLETED`, `CANCELLED`), `priority`, `owner_user_id`, `owner_agent_id`, `created_at`, `updated_at`, `completed_at`.
  * `Task` model (`tasks` table) with fields: `id`, `company_id`, `project_id`, `parent_task_id`, `title`, `description`, `objective`, `created_by_user_id`, `created_by_agent_id`, `assigned_to_agent_id`, `assigned_to_user_id`, `department_id`, `status` (12 authoritative statuses), `priority`, `deadline`, `output`, `error_details`, `created_at`, `started_at`, `completed_at`.
  * `TaskDependency` model (`task_dependencies` table) with foreign keys to `tasks.id` and unique constraint `uq_task_dependencies_pair`.
  * Added cascade relationships on `Company`: `projects`, `tasks`.
  * Created performance indexes for tenant scoping, status querying, and project/assignment lookups.
* **Database Migration (`database/migrations/versions/0006_create_projects_tasks.py`):**
  * Created revision `0006_create_projects_tasks`. Applied cleanly via `alembic upgrade head`. Reversibility verified with clean downgrade and re-upgrade. `alembic check` verified with 0 schema drift.
* **Domain Layer (`domain/work/`):**
  * Domain exceptions: `ProjectNotFoundError`, `TaskNotFoundError`, `WorkAccessDeniedError`, `InvalidStatusTransitionError`, `CircularDependencyError`, `SelfDependencyError`, `InvalidWorkAssignmentError`.
  * Status enumerations: `ProjectStatus`, `ProjectPriority`, `TaskStatus`, `TaskPriority`.
  * `TaskStateMachine`: Transition matrix enforcement across all 12 statuses and automatic `started_at` / `completed_at` timestamp management.
* **Application Services (`application/services/`):**
  * `ProjectService`: Project CRUD, task count rollup statistics, and tenant isolation.
  * `TaskService`: Task creation with project/parent links, automatic promotion from `CREATED` to `ASSIGNED` on specialist assignment, status transitions, assignment updates, prerequisite dependency management with graph reachability cycle prevention (rejecting $A \to B \to A$ and multi-node cycles), and company boundary checks.
  * Updated `SystemService`: `CURRENT_PHASE = "Phase 6 — Projects & Basic Tasks"`.
* **API Layer (`apps/api/`):**
  * Pydantic schemas in `apps/api/schemas/work.py`.
  * Project router mounted at `/api/v1/companies/{company_id}/projects` (`GET /`, `POST /`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`).
  * Task router mounted at `/api/v1/companies/{company_id}/tasks` (`GET /`, `POST /`, `GET /{id}`, `PATCH /{id}`, `PATCH /{id}/status`, `POST /{id}/assign`, `POST /{id}/dependencies`, `DELETE /{id}/dependencies/{dep_id}`, `DELETE /{id}`).
  * Routers registered in `apps/api/main.py`.
* **Frontend Web Application (`apps/web/`):**
  * Extended `apps/web/lib/api.ts` with project and task TypeScript interfaces and complete API methods.
  * Implemented Project Portfolio Console (`apps/web/app/projects/page.tsx`) with status filters, priority selector, search, project cards with progress bars and task stats, "New Project" modal, and project detail drawer.
  * Implemented Task Management Console (`apps/web/app/tasks/page.tsx`) adhering to `docs/UI.md` §§ 31 & 32 with multi-faceted filtering (status, project, department, agent, search), task table with human-readable IDs (`TASK-XXXXXX`), "New Task" modal, and Task Detail drawer with lifecycle state timeline, status progression buttons, assigned specialist link, dependency checklist, and output/error log view.
  * Updated Dashboard (`apps/web/app/page.tsx`): Active Projects and Open Tasks cards display live PostgreSQL counts, TopBar operational telemetry updated to `Operational · Phase 6 Active`, and honest `0` runtime active presence preserved.
* **Testing & Quality Assurance:**
  * Added 5 unit tests in `tests/unit/test_task_state_machine.py`.
  * Added 3 unit tests in `tests/unit/test_project_service.py`.
  * Added 4 unit tests in `tests/unit/test_task_service.py`.
  * Added comprehensive lifecycle & isolation integration test in `tests/integration/test_api_projects.py`.
  * Added comprehensive lifecycle & isolation integration test in `tests/integration/test_api_tasks.py`.
  * Added 2 frontend unit tests in `apps/web/lib/api.test.ts`.

### Phase 7 — Task Assignment & Delegation (COMPLETE)
* **Authoritative Persistence & Data Modeling (`infrastructure/database/models.py`):**
  * `DelegationRecord` model (`delegation_records` table) storing first-class audit records of every hierarchical task delegation:
    * `id`, `company_id`, `task_id`, `delegated_by_user_id` (optional), `delegated_by_agent_id` (optional), `delegated_to_agent_id` (required), `scope`, `reason`, `depth` (integer hop counter), `status`, `created_at`.
  * Added foreign key column `ceo_plans.project_id` linking strategic plans to decomposed projects upon delegation.
  * Added cascade relationships: `Company.delegation_records`, `Task.delegation_records`, and indexes on `(company_id, created_at)` and `(task_id, created_at)`.
* **Database Migration (`database/migrations/versions/0007_create_delegation_system.py`):**
  * Created migration `0007_create_delegation_system`. Applied cleanly to PostgreSQL via `alembic upgrade head`. Reversibility verified with downgrade/upgrade cycle. `alembic check` verified with 0 schema drift.
* **Domain Layer (`domain/delegation/`):**
  * Domain exceptions: `DelegationError`, `CircularDelegationError`, `MaxDelegationDepthExceededError`, `InvalidDelegationHierarchyError`, `DelegationAccessDeniedError`, `DelegationNotFoundError`.
  * `DelegationRuleEngine`: Enforces deterministic organizational hierarchy rules:
    * Tenant match: Delegator, delegatee, and task must belong to the same company.
    * Upward delegation rejection: Agents cannot delegate upward to their direct or indirect managers.
    * Department isolation: Department heads/leads can only delegate to agents within their own department.
    * Specialist restrictions: Specialists (authority level 1) cannot delegate further.
    * Circular delegation rejection: Traverses prior task delegation lineage and organizational ancestry to prevent cycles ($A \to B \to A$).
    * Maximum depth bound: Rejects delegations exceeding `max_depth = 3`.
    * Active agent checks: Rejects delegation to inactive agents.
* **Application Services (`application/services/`):**
  * `DelegationService`: Manages task delegation lifecycle, enforces domain validation rules, transitions task status to `ASSIGNED` with `assigned_to_agent_id`, creates immutable `DelegationRecord`, and retrieves chronological task lineages.
  * `CeoService.delegate_plan`: Bridges Phase 5 (CEO Plans) and Phase 6 (Projects/Tasks):
    * Validates CEO plan proposal state and converts it to 1 `Project`, 1 Parent `Task`, multiple Child `Task`s (`parent_task_id = parent_task.id`), and `TaskDependency` graph edges matching plan DAG steps.
    * Creates initial `DelegationRecord` entries for assigned tasks.
    * Attaches `project_id` to `CeoPlan` and marks status as `DELEGATED`.
  * Updated `SystemService`: `CURRENT_PHASE = "Phase 7 — Task Assignment & Delegation"`.
* **API Layer (`apps/api/`):**
  * Schemas: `TaskDelegateRequest`, `DelegationRecordResponse`, `DelegationListResponse`, `PlanDelegateRequest`, `PlanDelegationResultResponse` in `apps/api/schemas/delegation.py`.
  * Route handlers:
    * `POST /api/v1/companies/{company_id}/tasks/{task_id}/delegate`
    * `GET /api/v1/companies/{company_id}/tasks/{task_id}/delegations`
    * `GET /api/v1/companies/{company_id}/delegations`
    * `POST /api/v1/companies/{company_id}/ceo/plans/{plan_id}/delegate`
  * Routers mounted in `apps/api/main.py`.
* **Frontend Web Application (`apps/web/`):**
  * `apps/web/lib/api.ts`: Added `DelegationRecord`, `DelegationListResponse`, `PlanDelegationResult` interfaces and client methods `delegateTask`, `getTaskDelegations`, `listCompanyDelegations`, `delegatePlan`.
  * CEO Console (`apps/web/app/ceo/page.tsx`): Added "Delegate & Launch Workflows" button on proposed plans, status pill handling for `delegated`, and success notification banner linking to created project and decomposed tasks.
  * Task Console (`apps/web/app/tasks/page.tsx`): Added "Delegate Task" button and interactive inline delegation form, plus chronological "Delegation Lineage" timeline in Task Detail Drawer showing hops, depth badges, delegator $\to$ delegatee, directives, and timestamps.
  * Dashboard (`apps/web/app/page.tsx`): Updated operational indicators to `Phase 7 Active`.
* **Testing & Quality Assurance:**
  * Added 10 unit tests in `tests/unit/test_delegation_rules.py`.
  * Added 3 unit tests in `tests/unit/test_delegation_service.py`.
  * Added 1 unit test in `tests/unit/test_ceo_delegation.py`.
  * Added comprehensive lifecycle & isolation integration test in `tests/integration/test_api_delegation.py`.
  * Added 2 frontend client unit tests in `apps/web/lib/api.test.ts`.

### Phase 8 — Agent Runtime (Agent Execution Engine) (COMPLETE)
* **Authoritative Persistence & Database Models (`infrastructure/database/models.py`):**
  * Implemented `ExecutionRecord` SQLAlchemy model:
    * Primary key UUID `id`.
    * Foreign keys with `ON DELETE CASCADE`: `company_id`, `task_id`, `agent_id`.
    * Optional foreign key `executed_by_user_id` referencing triggering operator.
    * Status: `RUNNING`, `SUCCESS`, `FAILED`, `TIMED_OUT`.
    * Metrics: `step_count`, `duration_ms`, `tokens_used`, `estimated_cost` (Float).
    * Structured reasoning & outputs: `result_summary`, `deliverable` (Text), `steps_json` (JSON), `error_details`.
    * Timestamps: `created_at`, `completed_at`.
    * Indexes: `ix_execution_records_company_id`, `ix_execution_records_task_id`, `ix_execution_records_agent_id`, `ix_execution_records_status`.
    * Added `execution_records` relationships on `Company`, `Task`, and `Agent` models.
* **Database Migrations:**
  * Created Alembic migration `0008_create_execution_system.py`.
  * Verified forward upgrade, complete rollback (`downgrade -1`), and re-upgrade with 0 schema drift (`alembic check`).
* **Domain Runtime Engine (`domain/runtime/`):**
  * `schemas.py`: `RuntimeLimits` (`max_steps`, `max_duration_seconds`, `max_tokens`, `max_cost`), `ExecutionStep`, `Deliverable`, `ExecutionResult`, `AgentExecutionContext`.
  * `exceptions.py`: `ExecutionError`, `ExecutionTimeoutError`, `MaxStepsExceededError`, `AgentInactiveError`, `UnassignedTaskError`, `InvalidTaskStateForExecutionError`, `ExecutionAccessDeniedError`.
  * `engine.py`: `AgentRuntimeEngine` enforcing asynchronous timeout (`asyncio.wait_for`) and maximum step limits. Decoupled from LLM Gateway via `ExecutionGateway` protocol with lazy import.
* **LLM Gateway & Specialist Execution Provider:**
  * `infrastructure/llm/providers/base.py`: Abstract `execute_task(context, limits) -> ExecutionResult`.
  * `infrastructure/llm/providers/deterministic.py`: Implemented deterministic specialist execution for all 11 foundational agent roles (CTO, Lead Architect, Backend Specialist, Frontend Specialist, QA Specialist, DevOps Specialist, CMO, Content Specialist, Head of Sales, Lead Financial Analyst, Head of Operations) with role-tailored step transcripts and verified deliverables.
  * `infrastructure/llm/gateway.py`: Added `execute_agent_task(context, limits)`.
* **Application Services:**
  * `application/services/execution_service.py`:
    * Multi-tenant membership verification and tenant isolation.
    * Validates assigned agent is present and active.
    * Validates executable task status (`ASSIGNED`, `READY`, `PLANNED`, `FAILED`).
    * Transitions task to `IN_PROGRESS`.
    * Persists `ExecutionRecord` in `RUNNING` status.
    * Assembles `AgentExecutionContext` (agent definition, task, company, prerequisites).
    * Invokes `AgentRuntimeEngine`.
    * **Enforces Phase 8 Golden Rule:** An agent claiming "Task completed" does **not** make the task `COMPLETED`; automatically transitions task to `VERIFYING`, records deliverable in `task.output`, and requires operator verification.
    * On failure: transitions task to `FAILED` with `task.error_details`.
    * Methods: `execute_task`, `list_task_executions`, `get_execution`.
  * `application/services/system_service.py`: Updated current phase telemetry to `Phase 8 — Agent Runtime`.
* **API Layer (`apps/api/`):**
  * `apps/api/schemas/execution.py`: `TaskExecuteRequest`, `ExecutionRecordResponse`, `ExecutionListResponse`.
  * `apps/api/routes/execution.py`:
    * `POST /api/v1/companies/{company_id}/tasks/{task_id}/execute`
    * `GET /api/v1/companies/{company_id}/tasks/{task_id}/executions`
    * `GET /api/v1/companies/{company_id}/executions/{execution_id}`
  * Routers mounted in `apps/api/main.py`.
* **Frontend Web Application (`apps/web/`):**
  * `apps/web/lib/api.ts`: Added `ExecutionRecord`, `ExecutionStep`, `ExecutionListResponse`, `TaskExecuteRequest` interfaces and client methods `executeTask`, `getTaskExecutions`, `getExecution`.
  * Task Console (`apps/web/app/tasks/page.tsx`):
    * Quick "Run" execution trigger on assigned tasks in task table.
    * "Phase 8 Verification Guard" alert banner in drawer when task status is `VERIFYING`, providing direct "Verify & Complete Task" action.
    * "Agent Runtime Engine" control panel in drawer with budget limits (`max_steps`, `max_duration_seconds`) and "Execute Agent" button with spinner.
    * "Execution Run History" chronological list with status badges, execution metrics (duration, steps, tokens, cost), expandable reasoning step transcripts (thought, action, observation), deliverable code blocks, and error details.
  * Dashboard (`apps/web/app/page.tsx`): Updated telemetry badges to `Phase 8 Active`.
* **Testing & Quality Assurance:**
  * Added 4 unit tests in `tests/unit/test_runtime_engine.py` (success, role deliverables, max steps exceeded, timeout guard).
  * Added 3 unit tests in `tests/unit/test_execution_service.py` (success lifecycle, validation guards, multi-company access denial).
  * Added comprehensive lifecycle & isolation integration test in `tests/integration/test_api_execution.py`.
  * Added 2 frontend client unit tests in `apps/web/lib/api.test.ts`.

### Phase 9 — Tool Gateway (Controlled External Tools) (COMPLETE)
* **Authoritative Persistence & Database Models (`infrastructure/database/models.py`):**
  * Implemented `ToolExecutionRecord` SQLAlchemy model:
    * Primary key UUID `id`.
    * Foreign keys with `ON DELETE CASCADE`: `company_id`, `agent_id`, optional `task_id`, optional `execution_id`.
    * Tool invocation metadata: `tool_name`, `action`, `risk_level` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), `requires_approval` (Boolean), `status` (`SUCCESS`, `FAILED`, `APPROVAL_REQUIRED`, `BLOCKED`).
    * Structured I/O & audit: `input_params` (sanitized JSON), `output_data` (normalized JSON), `error_details` (Text), `duration_ms` (Integer).
    * Timestamps & compound indexes: `ix_tool_execution_records_company_created`, `ix_tool_execution_records_agent_created`, `ix_tool_execution_records_task_created`, `ix_tool_execution_records_tool_name`.
    * Added `tool_execution_records` relationships on `Company`, `Agent`, `Task`, and `ExecutionRecord` models.
* **Database Migrations:**
  * Created Alembic migration `0009_create_tool_system.py`.
  * Verified forward upgrade, complete rollback (`downgrade -1`), and re-upgrade with 0 schema drift (`alembic check`).
* **Domain Tool Gateway Layer (`domain/tools/`):**
  * `schemas.py`: `ToolRiskLevel`, `ToolExecutionStatus`, `ToolDefinition`, `ToolCallRequest`, `ToolCallResult`, and normalized domain models: `SearchResultItem`, `SearchResult`, `DocumentContent`, `GitHubResult`.
  * `exceptions.py`: `ToolError`, `ToolNotFoundError`, `ToolValidationError`, `ToolPermissionDeniedError`, `ToolApprovalRequiredError`, `ToolExecutionFailedError`, `ToolAccessDeniedError`, `ToolExecutionNotFoundError`.
* **Tool Gateway Pipeline & Core Tools (`tools/`):**
  * `tools/gateway/validator.py`: `ToolValidator` enforcing JSON schema validation and regex pattern masking for secrets, tokens, API keys, and passwords.
  * `tools/gateway/permissions.py`: `ToolPermissionChecker` checking role-based access control and authority levels.
  * `tools/gateway/risk.py`: `ToolRiskEvaluator` assessing risk tiers and flagging actions that mandate human approval.
  * `tools/gateway/registry.py`: `ToolRegistry` maintaining available tools and role-based discovery.
  * `tools/gateway/gateway.py`: `ToolGateway` executing the 8-step security pipeline: sanitize parameters $\to$ lookup tool $\to$ validate schema $\to$ check permissions $\to$ evaluate risk $\to$ approval check $\to$ adapter execution $\to$ package normalized result.
  * **3 Foundational Tool Adapters:**
    1. `tools/web/search.py`: `WebSearchTool` returning normalized search results (`title`, `url`, `snippet`).
    2. `tools/documents/reader.py`: `DocumentsTool` providing verified internal document access (`architecture_spec`, `security_guidelines`).
    3. `tools/github/inspector.py`: `GitHubTool` providing repository inspection, branches, commits, and issues for engineering roles.
* **Application Services:**
  * `application/services/tool_service.py`:
    * Multi-tenant membership verification and tenant isolation.
    * Agent verification and active status validation.
    * Invocation of `ToolGateway` with caller role and authority level.
    * Immutable persistence of `ToolExecutionRecord` with sanitized inputs and normalized outputs.
    * Methods: `list_tools`, `get_tool`, `execute_tool`, `list_tool_executions`, `get_tool_execution`.
  * `application/services/system_service.py`: Updated current phase telemetry to `Phase 9 — Tool Gateway`.
* **API Layer (`apps/api/`):**
  * `apps/api/schemas/tool.py`: `ToolDefinitionResponse`, `ToolListResponse`, `ToolExecuteApiRequest`, `ToolExecutionResponse`, `ToolExecutionListResponse`.
  * `apps/api/routes/tool.py`:
    * `GET /api/v1/companies/{company_id}/tools`
    * `GET /api/v1/companies/{company_id}/tools/definitions/{tool_name}`
    * `POST /api/v1/companies/{company_id}/tools/execute`
    * `GET /api/v1/companies/{company_id}/tools/executions`
    * `GET /api/v1/companies/{company_id}/tools/executions/{execution_id}`
  * Routers mounted in `apps/api/main.py`.
* **Frontend Web Application (`apps/web/`):**
  * `apps/web/lib/api.ts`: Added `ToolDefinition`, `ToolListResponse`, `ToolExecuteRequest`, `ToolExecutionRecord`, `ToolExecutionListResponse` interfaces and client methods `getTools`, `getToolDefinition`, `executeTool`, `getToolExecutions`, `getToolExecution`.
  * `apps/web/app/tools/page.tsx`:
    * Tool Registry tab: cards for all registered tools with provider, version, risk badges, permitted roles, and quick test links.
    * Interactive Runner tab: agent selector, tool & action picker, presets for all tools (including approval demo), JSON parameter editor, live pipeline execution, normalized output inspector, and sanitized parameter preview.
    * Audit Trail tab: filterable, searchable table of immutable execution records with duration, risk level, status badges, and detail modal.
  * `apps/web/components/shell/Sidebar.tsx`: Added "Tool Gateway" navigation item under Work Management.
  * `apps/web/app/page.tsx`: Updated telemetry indicators to `Phase 9 Active`.
* **Testing & Quality Assurance:**
  * Added 5 unit tests in `tests/unit/test_tool_registry.py`.
  * Added 4 unit tests in `tests/unit/test_tool_validator.py`.
  * Added 6 unit tests in `tests/unit/test_tool_gateway.py`.
  * Added 6 unit tests in `tests/unit/test_tool_service.py`.
  * Added comprehensive lifecycle & isolation integration test in `tests/integration/test_api_tools.py`.
  * Added 3 frontend client unit tests in `apps/web/lib/api.test.ts`.

### Phase 10 — Approval & Oversight System (COMPLETE)
* **Domain Layer (`domain/approvals/`):**
  * `schemas.py`: Created authoritative enumerations `ApprovalStatus` (`PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`), `ApprovalActionType` (`SEND_EMAIL`, `PUBLISH_CONTENT`, `SPEND_MONEY`, `DELETE_DATA`, `DEPLOY_PRODUCTION`, `MODIFY_CONFIGURATION`, `EXTERNAL_COMMUNICATION`, `TOOL_EXECUTION`, `DATABASE_MIGRATION`, `HIGH_RISK_ACTION`), `ApprovalRiskLevel` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), `ApprovalDecision` (`APPROVED`, `REJECTED`), and Pydantic schemas `ApprovalRequestCreate`, `ApprovalDecisionInput`, and `ApprovalFilter`.
  * `exceptions.py`: Defined domain exceptions `ApprovalError`, `ApprovalNotFoundError`, `ApprovalAlreadyProcessedError`, `ApprovalAccessDeniedError`, `InvalidApprovalTransitionError`, and `AgentCannotApproveError`.
  * `state_machine.py`: Implemented `ApprovalStateMachine` enforcing valid transitions from `PENDING` to terminal states (`APPROVED`, `REJECTED`, `CANCELLED`) and permanently rejecting state tampering once terminal.
  * `policy_engine.py`: Implemented `ApprovalPolicyEngine` identifying consequential actions, evaluating tool-level gate requirements, enforcing financial spend thresholds, and strictly barring automated agents from reviewing approvals per docs/Rules.md § 42.
* **Database & Persistence:**
  * Added `ApprovalRequest` entity in `infrastructure/database/models.py` with foreign keys to `companies.id`, `tasks.id`, `agents.id`, `execution_records.id`, `tool_execution_records.id`, and `users.id` (reviewer).
  * Configured compound indexes `ix_approval_requests_company_status` and `ix_approval_requests_company_created`.
  * Authored Alembic migration `database/migrations/versions/0010_create_approval_system.py`, applied migration `0010`, validated bidirectional rollback, and verified 0 schema drift with `alembic check`.
* **Application Services:**
  * Built `ApprovalService` in `application/services/approval_service.py` managing `create_approval`, `list_approvals`, `get_approval`, `approve_request` (with automatic tool execution resumption and task state unblocking), and `reject_request` (with permanent blocking).
  * Updated `ToolService.execute_tool` in `application/services/tool_service.py` to automatically instantiate a `PENDING` `ApprovalRequest` and set task status to `APPROVAL_REQUIRED` whenever an action halts with `APPROVAL_REQUIRED` or `requires_approval=True`.
  * Enhanced `ToolGateway` in `tools/gateway/gateway.py` with `execute_approved` for clean post-approval adapter resumption.
  * Updated `SystemService` to report `CURRENT_PHASE = "Phase 10 — Approval System"`.
* **API Layer (`apps/api/`):**
  * Created Pydantic response schemas `ApprovalRequestResponse`, `ApprovalListResponse`, and `ApprovalDecisionRequest` in `apps/api/schemas/approval.py`.
  * Built RESTful route handlers in `apps/api/routes/approval.py`:
    * `GET /api/v1/companies/{company_id}/approvals` (listing with status, risk level, agent filters and pagination)
    * `GET /api/v1/companies/{company_id}/approvals/{approval_id}` (detailed inspection)
    * `POST /api/v1/companies/{company_id}/approvals/{approval_id}/approve` (human operator approval and execution release)
    * `POST /api/v1/companies/{company_id}/approvals/{approval_id}/reject` (human operator rejection and permanent block)
  * Registered router in `apps/api/main.py`.
* **Frontend UI Console (`apps/web/`):**
  * Updated `apps/web/lib/api.ts` with TypeScript interfaces `ApprovalRequest`, `ApprovalListResponse`, `ApprovalDecisionRequest` and API client methods `getApprovals`, `getApproval`, `approveRequest`, `rejectRequest`.
  * Replaced placeholder with full-featured Human Oversight & Approval Console in `apps/web/app/approvals/page.tsx`:
    * Live telemetry metric cards (Pending Actions, High/Critical Risk count, Total Approved, Total Rejected).
    * Filter bar with real-time status tabs and risk tier dropdown.
    * Interactive cards with status badges, risk indicators, agent/task attribution, and action descriptions.
    * Slide-over details drawer showing full JSON payload, audit timestamps, and reviewer rationale.
    * Authorize & Execute / Permanently Block decision modal with reviewer justification capture.
  * Updated `apps/web/app/page.tsx` Dashboard with live pending approvals count and alert badge.
  * Added 3 web client unit tests in `apps/web/lib/api.test.ts`.

---

## Verification Results

| Verification Item | Command / Harness | Result |
| :--- | :--- | :--- |
| **Backend Unit & Integration Tests** | `pytest tests/` | **PASSED** (121 passed in 12.59s) |
| **Approval Domain & Service Tests** | `pytest tests/unit/test_approval*.py tests/integration/test_api_approval.py` | **PASSED** (15 tests in 1.47s) |
| **Python Linting** | `ruff check .` | **PASSED** (0 errors across 155 files) |
| **Python Formatting** | `ruff format --check .` | **PASSED** (155 files compliant) |
| **Python Static Type Checking** | `mypy .` | **PASSED** (154 source files checked, 0 errors) |
| **Frontend Unit Tests** | `npm --prefix apps/web test -- --run` | **PASSED** (28 tests in 2 files in 263ms) |
| **Frontend Linting** | `npm --prefix apps/web run lint` | **PASSED** (0 errors, 0 warnings) |
| **Frontend Production Build** | `npm --prefix apps/web run build` | **PASSED** (15 routes compiled, static generation verified) |
| **Database Migrations** | `alembic upgrade head` | **PASSED** (Revisions `0001`–`0010` applied on PostgreSQL) |
| **Database Schema Drift** | `alembic check` | **PASSED** (No new upgrade operations detected) |
| **Authentication & Isolation Regression** | Automated test suite | **PASSED** (Multi-company data isolation, human-only approvals, agent rejection enforcement) |

---

## Important Architectural Decisions

1. **Human-Only Authority Enforcement (docs/Rules.md § 42):**
   Agents are strictly forbidden from approving or rejecting actions for themselves or other agents. Calling approval endpoints as an agent raises `AgentCannotApproveError` and returns `403 Forbidden`.
2. **Consequential Action Gating:**
   All actions designated as consequential (`SEND_EMAIL`, `PUBLISH_CONTENT`, `SPEND_MONEY`, `DELETE_DATA`, `DEPLOY_PRODUCTION`, `MODIFY_CONFIGURATION`, `EXTERNAL_COMMUNICATION`, `DATABASE_MIGRATION`, `HIGH_RISK_ACTION`) or classified as `HIGH`/`CRITICAL` risk automatically trigger approval interception.
3. **Bidirectional Tool Gateway Integration:**
   When a tool execution halts with `APPROVAL_REQUIRED`, an `ApprovalRequest` is created in PostgreSQL with `status="PENDING"`. When a human approves the request, `ApprovalService` resumes execution through `ToolGateway.execute_approved` and transitions the `ToolExecutionRecord` to `SUCCESS`. If rejected, execution is permanently marked `BLOCKED`.
4. **Task State Synchronization:**
   Tasks awaiting approval are moved to `TaskStatus.APPROVAL_REQUIRED`. Upon approval, tasks resume to `IN_PROGRESS`. Upon rejection, tasks transition to `BLOCKED`.
5. **Terminal State Immutability:**
   Once an approval request reaches `APPROVED`, `REJECTED`, or `CANCELLED`, it cannot transition to any other status. Attempting to review an already-processed approval raises `ApprovalAlreadyProcessedError` (`409 Conflict`).
6. **Runtime Active Presence Remains 0:**
   Active agent presence and long-lived background loops remain strictly at 0, reserved for Phase 14.

---

## Next Authorized Phase

**Phase 11 — Audit Logging & Compliance System**
*(Awaiting user authorization before proceeding).*



