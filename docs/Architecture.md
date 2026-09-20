# AI Company OS — System Architecture

**Document:** `ARCHITECTURE.md`
**Version:** 1.0
**Status:** Draft / Foundation
**Related Documents:** `PRD.md`, `RULES.md`
**Architecture Style:** Modular Monolith + Event-Driven Background Execution
**Primary Interface:** Voice + Web
**Primary Orchestrator:** CEO Agent

---

# 1. Architecture Overview

AI Company OS is a **voice-first, multi-agent company operating system**.

The system allows a user to communicate with an AI CEO.

The CEO:

1. understands the user's objective
2. loads relevant company state
3. determines what work is required
4. creates a plan
5. creates a task graph
6. delegates work
7. supervises department heads
8. monitors specialist agents
9. controls access to tools
10. waits for approvals where required
11. verifies important results
12. updates company state
13. reports the outcome to the user

The system is therefore not designed as a collection of independent chatbots.

It is designed as:

```text
                         ┌──────────────────────┐
                         │         USER         │
                         │   Voice / Web / API  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    EXPERIENCE LAYER  │
                         │ Voice + Web Dashboard│
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     API / GATEWAY    │
                         │ Auth / Rate Limiting │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     CEO ORCHESTRATOR │
                         │ Understand / Plan    │
                         │ Delegate / Supervise │
                         │ Verify / Report      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    TASK ENGINE       │
                         │ Plans / DAG / Queue  │
                         └──────────┬───────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
                  ▼                 ▼                 ▼
               ┌──────┐          ┌──────┐          ┌──────┐
               │ CTO  │          │ CMO  │          │Sales │
               └──┬───┘          └──┬───┘          └──┬───┘
                  │                 │                 │
                  ▼                 ▼                 ▼
             Specialists       Specialists       Specialists
                  │                 │                 │
                  └─────────────────┼─────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    AGENT RUNTIME     │
                         │ Context / LLM / Loop │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     POLICY ENGINE    │
                         │ Auth / Permissions   │
                         │ Risk / Approval      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     TOOL GATEWAY     │
                         └──────────┬───────────┘
                                    │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
           Web Search           GitHub                Email
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │   COMPANY STATE      │
                         │ PostgreSQL / Redis   │
                         │ Vector Retrieval     │
                         └──────────────────────┘
```

---

# 2. Architectural Goals

The architecture must provide:

* clear separation of responsibilities
* persistent company state
* reliable task execution
* controlled agent autonomy
* secure tool access
* human approval
* observability
* auditability
* recoverability
* extensibility
* testability

The architecture must also prevent the system from becoming a single giant LLM prompt.

---

# 3. Core Architectural Principles

## 3.1 CEO Is an Orchestrator

The CEO should coordinate work.

It should not directly perform every specialist task.

```text
CEO
 ↓
Department
 ↓
Specialist
 ↓
Tool
```

---

# 4. Company State Is External to the LLM

The LLM is not the source of truth.

The source of truth is the application state.

```text
PostgreSQL
     │
     ├── Company
     ├── Projects
     ├── Tasks
     ├── Agents
     ├── Approvals
     ├── Documents
     └── Audit Events
```

LLM context is reconstructed from that state.

---

# 5. Deterministic Security Boundary

AI decides what it wants to do.

Software decides whether it is allowed.

```text
Agent
  ↓
Requested Action
  ↓
Policy Engine
  ↓
Permission Check
  ↓
Approval Check
  ↓
Tool Gateway
```

The LLM must never be the final security authority.

---

# 6. Architecture Style

The initial implementation should use a:

**Modular Monolith**

rather than microservices.

This means:

```text
One deployable backend
        │
        ├── API
        ├── CEO
        ├── Orchestration
        ├── Agents
        ├── Tools
        ├── Policies
        ├── Memory
        └── Database
```

These components remain logically separated in code.

Later, high-load components can be extracted into independent services.

---

# 7. Why Modular Monolith First?

A distributed architecture introduces:

* network failures
* service discovery
* distributed tracing
* deployment complexity
* data synchronization
* distributed transactions

The initial product does not need this complexity.

The architecture should instead preserve future extraction boundaries.

---

# 8. High-Level Application Layers

The backend should follow:

```text
┌──────────────────────────────┐
│ Presentation / API           │
├──────────────────────────────┤
│ Application Services         │
├──────────────────────────────┤
│ Domain                       │
├──────────────────────────────┤
│ Orchestration                │
├──────────────────────────────┤
│ Agent Runtime                │
├──────────────────────────────┤
│ Policy / Security            │
├──────────────────────────────┤
│ Infrastructure               │
└──────────────────────────────┘
```

---

# 9. Layer Responsibilities

## 9.1 Presentation Layer

Responsible for:

* HTTP
* WebSocket/SSE
* request validation
* authentication
* response formatting

Should not contain business logic.

---

## 9.2 Application Layer

Coordinates use cases.

Examples:

```text
CreateProject
CreateTask
RunAgent
ApproveAction
CancelTask
GetCompanyStatus
```

---

## 9.3 Domain Layer

Contains core business concepts:

* Company
* Agent
* Department
* Task
* Project
* Approval
* Artifact
* Decision

The domain should not depend directly on FastAPI or external vendors.

---

# 10. Orchestration Layer

Responsible for:

* planning
* delegation
* task graph creation
* scheduling
* execution
* recovery
* supervision

This is the operational brain around the LLM.

---

# 11. Agent Runtime

Responsible for running an individual agent.

Conceptually:

```text
Agent Definition
      +
Task
      +
Company Context
      +
Permissions
      +
Tools
      +
Memory
      ↓
Agent Runtime
      ↓
LLM
      ↓
Structured Output
```

---

# 12. Infrastructure Layer

Contains:

* PostgreSQL
* Redis
* LLM providers
* external APIs
* object storage
* vector retrieval
* email
* GitHub
* web search

---

# 13. Complete Request Flow

A normal voice request follows this path:

```text
User speaks
    ↓
Microphone
    ↓
Speech-to-Text
    ↓
Conversation Service
    ↓
API
    ↓
CEO Agent
    ↓
Intent Analysis
    ↓
Company State Retrieval
    ↓
Planning
    ↓
Task Graph
    ↓
Policy Check
    ↓
Task Dispatch
    ↓
Department Head
    ↓
Specialist Agent
    ↓
Agent Runtime
    ↓
Tool Gateway
    ↓
External Tool
    ↓
Tool Result
    ↓
Agent Result
    ↓
Verification
    ↓
Task Completion
    ↓
Company State Update
    ↓
CEO
    ↓
Text Response
    ↓
Text-to-Speech
    ↓
User
```

---

# 14. Detailed Voice Flow

```text
┌───────────────┐
│ Microphone    │
└───────┬───────┘
        │
        ▼
┌────────────────┐
│ Speech-to-Text │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Conversation    │
│ Manager        │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ CEO Agent      │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Task Engine    │
└───────┬────────┘
        │
        ▼
     Execution
        │
        ▼
┌────────────────┐
│ CEO Response   │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Text-to-Speech │
└───────┬────────┘
        │
        ▼
     Speaker
```

---

# 15. Text Request Flow

The same architecture must work without voice.

```text
Web UI
  ↓
POST /chat
  ↓
Conversation Service
  ↓
CEO
  ↓
Task Engine
```

Voice is an interface, not a separate business architecture.

---

# 16. CEO Execution Architecture

The CEO should have several internal stages.

```text
CEO
│
├── Intent Understanding
│
├── Context Retrieval
│
├── Planning
│
├── Delegation
│
├── Monitoring
│
├── Verification
│
├── Escalation
│
└── Reporting
```

---

# 17. CEO Intent Understanding

Input:

> "Research Germany for our AI product."

The CEO should determine:

```text
Objective:
Evaluate German market opportunity.

Desired outcome:
Research report + recommendation.

Potential departments:
CMO
Sales
Finance
CTO
```

The CEO should not immediately execute tools before understanding the objective.

---

# 18. Company Context Retrieval

Before planning, the CEO retrieves relevant context.

Example:

```text
Company Mission
Product Information
Current Strategy
Existing Research
Previous Decisions
Current Projects
Relevant Customer Data
```

Only relevant context should be loaded.

---

# 19. Planning

The planner transforms:

```text
Objective
```

into:

```text
Plan
```

Example:

```text
Goal
 ├── Market Research
 ├── Customer Research
 ├── Competitor Research
 ├── Financial Analysis
 └── Technical Analysis
```

---

# 20. Task Graph

The planner produces a DAG.

```text
Market Research ─────┐
Customer Research ───┤
Competitor Research ─┼──> Market Synthesis
Financial Analysis ──┤
Technical Analysis ──┘
                           │
                           ▼
                       CEO Review
```

No circular dependencies are allowed.

---

# 21. Task Dispatcher

The dispatcher determines:

```text
Which agent?
Which department?
Which worker?
When?
With what context?
With which tools?
```

Example:

```text
Task:
Market Research

Department:
Marketing

Agent:
Marketing Strategist
```

---

# 22. Agent Runtime Flow

```text
Task
 ↓
Agent Definition
 ↓
Load Permissions
 ↓
Load Context
 ↓
Load Relevant Memory
 ↓
Construct Prompt
 ↓
Call LLM
 ↓
Parse Structured Output
 ↓
Validate Output
 ↓
Execute Requested Tools
 ↓
Validate Tool Results
 ↓
Repeat if necessary
 ↓
Produce Final Result
```

---

# 23. Agent Loop

Conceptually:

```text
Observe
  ↓
Reason
  ↓
Plan next action
  ↓
Check permission
  ↓
Call tool
  ↓
Observe result
  ↓
Continue / finish
```

The loop must be bounded.

---

# 24. Agent Execution Limits

Every run should have:

```text
max_steps
max_tool_calls
max_retries
max_duration
max_tokens
max_cost
max_delegation_depth
```

If a limit is reached:

```text
STOP
 ↓
SAVE STATE
 ↓
REPORT
 ↓
ESCALATE
```

---

# 25. Department Architecture

Each department is a logical organization.

Example:

```text
CMO
│
├── Marketing Strategist
├── Copywriter
├── SEO Specialist
└── Social Media Specialist
```

Department heads:

* receive tasks from CEO
* create subtasks
* delegate to specialists
* review outputs
* report upward

---

# 26. Agent Hierarchy

```text
Owner
  ↓
CEO
  ↓
Department Head
  ↓
Specialist
```

Specialists should not normally bypass their department head.

Exceptions can be explicitly defined for urgent or specialized workflows.

---

# 27. Agent Definition Architecture

Each agent definition should be stored as configuration.

Example:

```text
agents/
└── departments/
    └── cmo/
        ├── agent.yaml
        ├── prompt.md
        ├── policies.yaml
        └── README.md
```

---

# 28. Agent Configuration

An agent definition should specify:

```text
id
name
type
reports_to
mission
responsibilities
skills
tools
permissions
authority
approval_requirements
success_metrics
failure_policy
escalation_rules
```

---

# 29. Tool Architecture

Tools should be adapters around external capabilities.

```text
tools/
├── web/
├── github/
├── email/
├── calendar/
├── documents/
└── database/
```

Each tool should have a common interface.

Conceptually:

```python
class Tool:
    name
    description
    risk_level

    async def validate_input(...)
    async def execute(...)
    async def validate_output(...)
```

---

# 30. Tool Gateway

All tool calls should pass through:

```text
Tool Gateway
```

The gateway performs:

1. authentication
2. authorization
3. policy validation
4. approval validation
5. input validation
6. execution
7. output validation
8. audit logging

---

# 31. Tool Execution Flow

```text
Agent
 ↓
Tool Request
 ↓
Schema Validation
 ↓
Permission Check
 ↓
Risk Classification
 ↓
Approval Check
 ↓
Credential Resolution
 ↓
Tool Execution
 ↓
Output Validation
 ↓
Audit Log
 ↓
Agent
```

---

# 32. Policy Engine

The policy engine is deterministic.

Inputs:

```text
agent
action
resource
risk
company
user
approval
environment
```

Output:

```text
ALLOW
DENY
REQUIRE_APPROVAL
```

---

# 33. Permission Model

Permissions should support:

```text
READ
WRITE
EXECUTE
EXTERNAL
SENSITIVE
IRREVERSIBLE
```

Example:

```yaml
cmo:
  web_search: allow
  create_document: allow
  publish_campaign: approval_required
  spend_money: approval_required
```

---

# 34. Approval Architecture

```text
Agent requests action
        ↓
Policy Engine
        ↓
Approval Required
        ↓
Approval Record Created
        ↓
User Notified
        ↓
User Decision
        ↓
Policy Re-evaluated
        ↓
Action Executed
```

Approvals should be persisted.

---

# 35. Task State Architecture

The task state machine should be explicit.

```text
CREATED
   ↓
PLANNED
   ↓
READY
   ↓
ASSIGNED
   ↓
IN_PROGRESS
   ├── WAITING
   ├── BLOCKED
   └── APPROVAL_REQUIRED
           │
           ▼
        APPROVED
           │
           ▼
       IN_PROGRESS
           │
           ▼
       VERIFYING
           │
           ▼
        VERIFIED
           │
           ▼
       COMPLETED
```

Failure path:

```text
IN_PROGRESS
     ↓
FAILED
     ↓
Recovery
     ├── Retry
     ├── Replan
     ├── Reassign
     └── Escalate
```

---

# 36. Task Persistence

Every task must be persisted.

The worker must never rely only on in-memory state.

This enables:

* restart recovery
* retries
* monitoring
* audit
* historical reporting

---

# 37. Background Worker Architecture

Long-running tasks should execute outside the HTTP request lifecycle.

```text
API
 ↓
Create Task
 ↓
Database
 ↓
Queue
 ↓
Worker
 ↓
Agent Runtime
 ↓
Result
 ↓
Database
```

---

# 38. Queue Architecture

Redis can initially be used for:

* job queue
* cache
* distributed locks
* temporary state

PostgreSQL remains the source of truth.

---

# 39. Event Architecture

Important events should be emitted.

Examples:

```text
TaskCreated
TaskAssigned
TaskStarted
TaskBlocked
TaskCompleted
TaskFailed

ApprovalRequested
ApprovalGranted
ApprovalRejected

AgentStarted
AgentCompleted
AgentFailed

ToolCalled
ToolFailed
ToolCompleted
```

These events support:

* notifications
* analytics
* auditing
* real-time UI updates

---

# 40. Event Flow

```text
Task Engine
     │
     ▼
Event Bus / Event Dispatcher
     │
 ┌───┼───────────┐
 ▼   ▼           ▼
UI  Audit      Metrics
```

The initial implementation can use an internal event dispatcher rather than introducing a dedicated distributed event platform.

---

# 41. Company State Architecture

The company state should be divided into:

```text
Company
├── Organization
├── Strategy
├── Policies
├── Projects
├── Tasks
├── Customers
├── Documents
├── Decisions
├── Agents
├── Approvals
└── Integrations
```

---

# 42. Database Architecture

Primary database:

```text
PostgreSQL
```

Conceptual schema:

```text
users
companies
departments
agents

projects
tasks
task_dependencies

approvals
tool_executions

documents
artifacts
decisions

conversations
messages

memories
audit_events

integrations
notifications
```

---

# 43. PostgreSQL Responsibilities

PostgreSQL stores authoritative structured state.

Use it for:

* users
* companies
* permissions
* tasks
* projects
* agents
* approvals
* audit events
* structured business data

---

# 44. Vector Search

Use vector retrieval for:

* documents
* research
* semantic company knowledge
* previous reports
* unstructured notes

Possible implementation:

```text
PostgreSQL
+
pgvector
```

This reduces infrastructure complexity.

---

# 45. Vector Search Boundary

Vector retrieval should answer:

> "What information might be relevant?"

It must not answer:

> "Is this agent allowed to spend €1,000?"

Permissions must come from authoritative structured state.

---

# 46. Memory Architecture

```text
             MEMORY
                │
      ┌─────────┼─────────┐
      ▼         ▼         ▼
   Company    Project    Agent
   Memory     Memory     Memory
      │         │         │
      └─────────┼─────────┘
                ▼
          Retrieval Layer
                │
                ▼
          Agent Context
```

---

# 47. Context Assembly

Agent context should be assembled dynamically.

```text
Task
 +
Company Context
 +
Project Context
 +
Relevant Documents
 +
Relevant Memories
 +
Permissions
 +
Tool Definitions
 =
Agent Context
```

Do not send the entire company database to every agent.

---

# 48. LLM Gateway

The application should abstract model providers.

```text
Agent Runtime
      ↓
LLM Gateway
      ↓
Model Router
      ↓
Provider Adapter
      ↓
LLM Provider
```

---

# 49. Model Routing

Different tasks may require different models.

Example:

```text
Simple classification
→ lightweight model

Complex planning
→ stronger reasoning model

Large document analysis
→ long-context model

Voice interaction
→ realtime/voice model
```

Model selection should be configurable.

---

# 50. LLM Request Lifecycle

```text
Agent
 ↓
Prompt Builder
 ↓
Context Builder
 ↓
Model Router
 ↓
LLM Gateway
 ↓
Provider
 ↓
Structured Output Parser
 ↓
Schema Validation
 ↓
Agent Runtime
```

---

# 51. Structured Output

Agent outputs should use Pydantic schemas.

Example:

```python
class TaskResult(BaseModel):
    status: Literal["completed", "blocked", "failed"]

    summary: str
    evidence: list[str]
    artifacts: list[str]
    needs_approval: bool
```

This reduces ambiguity between AI output and application logic.

---

# 52. Prompt Architecture

Prompts should be assembled from components.

```text
System Rules
+
Agent Identity
+
Agent Mission
+
Task
+
Company Context
+
Relevant Memory
+
Tool Definitions
+
Output Schema
+
Safety Rules
```

Do not maintain one enormous CEO prompt containing the entire application.

---

# 53. Prompt Versioning

Every important agent execution should record:

```text
agent_version
prompt_version
model
model_configuration
tool_version
policy_version
```

This makes executions reproducible and debuggable.

---

# 54. Conversation Architecture

Conversation data:

```text
Conversation
 ├── User
 ├── Messages
 ├── Context
 ├── Active Project
 └── Active Task
```

Conversation history is not the same thing as company memory.

---

# 55. Conversation Context

The system should track:

```text
current topic
current project
current task
recent references
user intent
pending approvals
```

This supports follow-up commands.

Example:

```text
User:
"Show enterprise sales."

CEO:
"..."

User:
"Sort by value."

```

The second message should resolve against the active context.

---

# 56. Web Application Architecture

Frontend:

```text
Next.js
   │
   ├── Dashboard
   ├── Company
   ├── Agents
   ├── Projects
   ├── Tasks
   ├── Approvals
   ├── Activity
   └── Settings
```

---

# 57. Frontend Data Flow

```text
React UI
   ↓
TanStack Query
   ↓
API Client
   ↓
FastAPI
   ↓
Application Services
```

Real-time updates:

```text
Backend
 ↓
SSE/WebSocket
 ↓
Frontend Event Handler
 ↓
Query Cache Update
```

---

# 58. Voice UI

The voice interface should expose:

```text
Push to Talk
or
Voice Conversation
```

The UI should show:

```text
Listening
Processing
Thinking
Executing
Waiting
Speaking
```

This prevents the user from wondering what the system is doing.

---

# 59. Voice Interruption

The user should eventually be able to interrupt the CEO while speaking.

Example:

```text
CEO:
"I've reviewed the marketing..."

User:
"Stop. Show me the numbers."

CEO:
"Understood."
```

This requires a streaming conversational architecture.

---

# 60. Real-Time Architecture

```text
Browser
   │
   ├── HTTPS
   │
   └── WebSocket/SSE
          │
          ▼
       FastAPI
          │
          ▼
       Event Layer
          │
          ├── Agent events
          ├── Task events
          └── Approval events
```

---

# 61. Authentication

Authentication should happen before application actions.

Conceptually:

```text
User
 ↓
Authentication
 ↓
Session / Token
 ↓
Company Membership
 ↓
Authorization
 ↓
API
```

---

# 62. Authorization

Authorization must verify:

```text
Who is the user?
Which company?
Which role?
Which resource?
Which action?
```

---

# 63. Multi-Tenancy

Every company-owned record should be associated with:

```text
company_id
```

Queries must enforce company isolation.

This includes:

* tasks
* documents
* agents
* memory
* approvals
* integrations
* audit logs

---

# 64. Integration Architecture

External systems should be represented as integrations.

```text
Company
 └── Integration
       ├── provider
       ├── credentials
       ├── configuration
       └── status
```

Examples:

```text
GitHub
Google Calendar
Email provider
CRM
Slack
Cloud provider
```

---

# 65. Integration Adapter

Each integration should have an adapter.

```text
Tool
 ↓
Integration Adapter
 ↓
Provider API
```

This prevents provider-specific code from leaking throughout the application.

---

# 66. GitHub Architecture

```text
Engineering Agent
      ↓
GitHub Tool
      ↓
GitHub Adapter
      ↓
GitHub API
```

Supported operations can include:

* repository inspection
* issue creation
* branch creation
* pull request creation
* pull request inspection

Production deployment remains outside unrestricted agent authority.

---

# 67. Email Architecture

```text
Agent
 ↓
Email Tool
 ↓
Permission
 ↓
Approval if required
 ↓
Email Provider
```

The system should distinguish:

```text
Draft
Prepared
Approved
Sent
Failed
```

---

# 68. Calendar Architecture

Calendar operations should support:

* availability lookup
* event drafting
* event creation
* event updates
* cancellation

External changes should be auditable.

---

# 69. Document Architecture

Documents should support:

```text
create
read
update
version
archive
search
```

Documents should maintain version history where necessary.

---

# 70. Artifact Architecture

Artifacts are outputs created by tasks.

Examples:

```text
research_report.pdf
launch_plan.md
architecture.md
sales_analysis.xlsx
code_patch
marketing_copy.md
```

Artifacts should be linked to:

```text
task
project
agent
creator
version
evidence
```

---

# 71. Verification Architecture

Important outputs should move through:

```text
Agent Result
 ↓
Schema Validation
 ↓
Evidence Validation
 ↓
Business Validation
 ↓
Optional Independent Verification
 ↓
Verified Result
```

Only verified results should be treated as authoritative where verification is required.

---

# 72. Verification Strategies

Different tasks can have different verification methods.

### Code

* tests
* lint
* type checks
* review

### Data

* schema validation
* consistency checks

### Research

* source validation
* cross-source comparison

### External actions

* provider confirmation
* resulting state check

---

# 73. Error Architecture

Errors should flow through a centralized error model.

```text
Tool Error
 ↓
Error Classifier
 ↓
Retry?
 ↓
Recovery Strategy
 ↓
Task State
 ↓
User / CEO
```

---

# 74. Error Recovery

Possible strategies:

```text
RETRY
REPLAN
REASSIGN
WAIT
REQUEST_APPROVAL
ASK_USER
FAIL
```

---

# 75. Retry Policy

Retry only errors that are likely transient.

Example:

```text
Network timeout → Retry
Rate limit → Backoff + Retry
Invalid input → Fix or Fail
Permission denied → Stop
Approval required → Wait
Unknown external state → Verify
```

---

# 76. Idempotency Architecture

External operations should use idempotency keys where supported.

Example:

```text
company_id
task_id
operation_id
```

This helps prevent duplicate external actions after retries.

---

# 77. Distributed Locking

Redis can provide locks for operations such as:

```text
project execution
task assignment
agent execution
integration synchronization
```

Locks should have expiration.

---

# 78. Scheduling

The scheduler should support:

* immediate execution
* delayed execution
* recurring tasks
* deadlines
* dependencies
* priority

Example:

```text
Every Monday
→ Sales Agent
→ generate weekly sales report
→ CEO reviews
→ notify user
```

---

# 79. Proactive Execution

Later, the system should support event-driven workflows.

Example:

```text
Sales conversion falls below threshold
          ↓
Event generated
          ↓
CEO notified
          ↓
CEO creates investigation task
          ↓
Sales Analyst
          ↓
Report
```

---

# 80. Observability Architecture

Every important operation should produce structured telemetry.

```text
Application
   │
   ├── Logs
   ├── Metrics
   ├── Traces
   └── Audit Events
```

---

# 81. Logging

Logs should contain structured fields such as:

```text
timestamp
request_id
company_id
user_id
agent_id
task_id
tool
operation
status
duration
error
```

Never log secrets.

---

# 82. Tracing

A user request should be traceable through:

```text
User Request
 ↓
CEO
 ↓
Task
 ↓
Agent
 ↓
Tool
 ↓
External API
```

A correlation ID should connect these events.

---

# 83. Audit Logging vs Application Logging

These are different.

### Application logs

Used for debugging.

### Audit logs

Used to answer:

> "Who performed this action and why?"

Audit logs should be durable and protected from ordinary application mutation.

---

# 84. Cost Tracking

Every model execution should record:

```text
provider
model
input_tokens
output_tokens
estimated_cost
duration
task_id
agent_id
```

This allows per-company and per-project cost analysis.

---

# 85. Security Architecture

Security boundaries:

```text
Internet
   ↓
API Gateway
   ↓
Authentication
   ↓
Authorization
   ↓
Application
   ↓
Policy Engine
   ↓
Tool Gateway
   ↓
External Services
```

Agent execution should not bypass these boundaries.

---

# 86. Secret Management

Secrets should be stored outside:

* source code
* prompts
* agent memory
* database records visible to agents
* logs

Use a proper secret-management mechanism in production.

---

# 87. Prompt Injection Boundary

External text is always treated as untrusted.

```text
Web Page
Email
Document
GitHub Issue
Customer Message
       ↓
UNTRUSTED DATA
       ↓
Agent Context
```

It must never automatically modify:

* system instructions
* permissions
* approval state
* company policies

---

# 88. Code Execution Sandbox

Code-running agents should operate inside a sandbox.

Sandbox restrictions should cover:

```text
filesystem
network
CPU
memory
processes
execution time
credentials
```

---

# 89. Production Safety

Production systems should require stronger authorization.

```text
Development
   ↓
Testing
   ↓
Staging
   ↓
Production
```

Agent authority should decrease as impact increases.

---

# 90. Deployment Architecture

Initial production deployment:

```text
                    Internet
                       │
                       ▼
                Reverse Proxy
                       │
              ┌────────┴────────┐
              ▼                 ▼
           Next.js           FastAPI
                                │
                     ┌──────────┼──────────┐
                     ▼          ▼          ▼
                PostgreSQL    Redis      Workers
                                             │
                                             ▼
                                        Agent Runtime
```

---

# 91. Containerization

Services should be container-friendly.

Potential containers:

```text
web
api
worker
scheduler
postgres
redis
```

For local development these can be run through a single development environment.

---

# 92. Environment Architecture

At minimum:

```text
development
staging
production
```

Each environment should have separate:

* credentials
* databases
* integrations
* configuration

---

# 93. CI/CD

CI should execute:

```text
Install
 ↓
Lint
 ↓
Type Check
 ↓
Unit Tests
 ↓
Integration Tests
 ↓
Build
 ↓
Security Checks
 ↓
Deploy
```

Production deployment should be controlled.

---

# 94. Repository Architecture

Recommended repository:

```text
ai-company/
│
├── apps/
│   ├── api/
│   └── web/
│
├── agents/
│   ├── executive/
│   ├── departments/
│   └── specialists/
│
├── orchestration/
│   ├── planner/
│   ├── task_graph/
│   ├── delegation/
│   ├── scheduler/
│   ├── executor/
│   └── recovery/
│
├── domain/
│   ├── company/
│   ├── agents/
│   ├── projects/
│   ├── tasks/
│   ├── approvals/
│   └── artifacts/
│
├── application/
│   ├── commands/
│   ├── queries/
│   └── services/
│
├── infrastructure/
│   ├── database/
│   ├── llm/
│   ├── cache/
│   ├── storage/
│   └── integrations/
│
├── tools/
│   ├── web/
│   ├── github/
│   ├── email/
│   ├── calendar/
│   ├── documents/
│   └── database/
│
├── policies/
│   ├── permissions/
│   ├── approvals/
│   └── risk/
│
├── memory/
│   ├── retrieval/
│   ├── company/
│   ├── projects/
│   └── agents/
│
├── database/
│   ├── migrations/
│   └── seeds/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── agent/
│   └── security/
│
├── docs/
│
├── PRD.md
├── RULES.md
├── ARCHITECTURE.md
├── API.md
├── DATABASE.md
├── SECURITY.md
├── AGENTS.md
├── TOOLS.md
├── DEPLOYMENT.md
├── CONTRIBUTING.md
└── README.md
```

---

# 95. Detailed Folder Architecture

## `/apps`

Application entry points.

```text
apps/
├── api/
└── web/
```

---

# 96. `/apps/api`

Backend API.

```text
apps/api/
├── main.py
├── dependencies.py
├── middleware.py
├── routes/
├── schemas/
└── handlers/
```

---

# 97. `/apps/web`

Frontend application.

```text
apps/web/
├── app/
├── components/
├── features/
├── hooks/
├── lib/
├── services/
└── types/
```

---

# 98. `/agents`

Agent definitions.

```text
agents/
├── executive/
│   └── ceo/
│
├── departments/
│   ├── cto/
│   ├── cmo/
│   ├── sales/
│   ├── finance/
│   └── operations/
│
└── specialists/
    ├── engineering/
    ├── marketing/
    ├── sales/
    └── operations/
```

---

# 99. `/orchestration`

Controls execution.

```text
orchestration/
├── planner/
├── task_graph/
├── delegation/
├── scheduler/
├── executor/
├── supervisor/
└── recovery/
```

---

# 100. `/domain`

Contains business entities and rules.

```text
domain/
├── company/
├── agents/
├── tasks/
├── projects/
├── approvals/
├── documents/
└── artifacts/
```

---

# 101. `/application`

Contains application use cases.

Example:

```text
application/
├── commands/
│   ├── create_task.py
│   ├── assign_task.py
│   ├── approve_action.py
│   └── cancel_task.py
│
├── queries/
│   ├── get_company.py
│   ├── get_task.py
│   └── get_agent_status.py
│
└── services/
    ├── company_service.py
    ├── project_service.py
    └── approval_service.py
```

---

# 102. `/infrastructure`

External implementation details.

```text
infrastructure/
├── database/
├── llm/
├── cache/
├── storage/
├── queues/
└── integrations/
```

---

# 103. `/tools`

AI-accessible capabilities.

```text
tools/
├── base/
├── web/
├── github/
├── email/
├── calendar/
├── documents/
└── database/
```

---

# 104. `/policies`

Deterministic policies.

```text
policies/
├── permissions/
├── approvals/
├── risk/
├── spending/
└── environments/
```

---

# 105. `/memory`

Memory and retrieval.

```text
memory/
├── company/
├── project/
├── agent/
├── customer/
├── retrieval/
└── indexing/
```

---

# 106. `/tests`

Testing architecture.

```text
tests/
├── unit/
├── integration/
├── e2e/
├── agent/
├── security/
├── policies/
└── performance/
```

---

# 107. Agent Runtime File Structure

A specialist may eventually have:

```text
agents/specialists/marketing/strategist/
│
├── agent.yaml
├── prompt.md
├── policies.yaml
├── tools.yaml
├── evaluation.yaml
├── examples/
│   ├── successful_task.json
│   └── failure_task.json
└── README.md
```

---

# 108. CEO File Structure

```text
agents/executive/ceo/
├── agent.yaml
├── prompt.md
├── policies.yaml
├── planning.yaml
├── delegation.yaml
├── escalation.yaml
└── README.md
```

---

# 109. Task Engine File Structure

```text
orchestration/task_graph/
├── models.py
├── builder.py
├── validator.py
├── dependency.py
├── executor.py
└── state_machine.py
```

---

# 110. Planner File Structure

```text
orchestration/planner/
├── planner.py
├── schemas.py
├── context.py
├── decomposition.py
├── dependency_builder.py
└── validator.py
```

---

# 111. Tool Gateway File Structure

```text
tools/
├── gateway/
│   ├── gateway.py
│   ├── registry.py
│   ├── validator.py
│   ├── permissions.py
│   ├── risk.py
│   └── audit.py
│
├── web/
├── github/
├── email/
├── calendar/
└── documents/
```

---

# 112. API Architecture

API routes should be grouped by domain.

```text
routes/
├── auth.py
├── company.py
├── agents.py
├── projects.py
├── tasks.py
├── approvals.py
├── voice.py
├── conversations.py
├── documents.py
└── activity.py
```

---

# 113. API Request Lifecycle

```text
HTTP Request
 ↓
Middleware
 ↓
Authentication
 ↓
Authorization
 ↓
Schema Validation
 ↓
Application Service
 ↓
Domain
 ↓
Infrastructure
 ↓
Response
```

---

# 114. API Should Not Execute Long Agent Runs Directly

Bad:

```text
POST /task
   ↓
Run 20-minute agent execution
   ↓
Return response
```

Better:

```text
POST /task
   ↓
Create task
   ↓
Return task_id
   ↓
Worker executes
   ↓
Client receives updates
```

---

# 115. Real-Time Task Updates

The UI should subscribe to:

```text
/task/{id}/events
```

or equivalent WebSocket/SSE channels.

Events:

```text
task.started
agent.started
tool.started
tool.completed
agent.completed
task.blocked
task.completed
task.failed
approval.required
```

---

# 116. Data Flow

A complete business workflow looks like:

```text
USER INTENT
    ↓
Conversation
    ↓
CEO
    ↓
Context Retrieval
    ↓
Planner
    ↓
Task Graph
    ↓
Policy Engine
    ↓
Dispatcher
    ↓
Agent Runtime
    ↓
Tool Gateway
    ↓
External System
    ↓
Tool Result
    ↓
Agent
    ↓
Verification
    ↓
Task State
    ↓
Project State
    ↓
CEO
    ↓
User
```

---

# 117. Example Data Flow — Market Research

```text
User:
"Research Germany."

        ↓

CEO

        ↓

Project:
Germany Market Evaluation

        ↓

Tasks:

T1 Market Research
T2 Customer Research
T3 Competitor Research
T4 Financial Research

        ↓

Workers

        ↓

Agents

        ↓

Web Tool

        ↓

Sources

        ↓

Research Artifacts

        ↓

Verification

        ↓

CEO Synthesis

        ↓

Report
```

---

# 118. Example Data Flow — Coding

```text
User:
"Fix the login bug."

        ↓

CEO

        ↓

CTO

        ↓

Engineer

        ↓

GitHub Tool

        ↓

Repository

        ↓

Code Change

        ↓

Tests

        ↓

Pull Request

        ↓

Verification

        ↓

CEO

        ↓

User
```

---

# 119. Example Data Flow — External Email

```text
User:
"Email the customer."

        ↓

CEO

        ↓

Sales Agent

        ↓

Draft Email

        ↓

Approval Policy

        ↓

Approval Required?

      YES
       ↓
User Approval
       ↓
Email Gateway
       ↓
Provider
       ↓
Delivery Confirmation
       ↓
Audit
```

---

# 120. Architecture Boundaries

The following boundaries must remain explicit:

```text
Frontend
   ≠
Backend

Backend
   ≠
LLM

LLM
   ≠
Permission System

Agent
   ≠
Tool

Tool
   ≠
External Provider

Memory
   ≠
Source of Truth

Conversation
   ≠
Company State
```

---

# 121. Technology Stack Summary

| Layer          | Technology                         |
| -------------- | ---------------------------------- |
| Frontend       | Next.js                            |
| UI             | React                              |
| Language       | TypeScript                         |
| Styling        | Tailwind CSS                       |
| Frontend State | TanStack Query / Zustand           |
| Backend        | Python                             |
| API            | FastAPI                            |
| Validation     | Pydantic                           |
| ORM            | SQLAlchemy                         |
| Migrations     | Alembic                            |
| Database       | PostgreSQL                         |
| Vector Search  | pgvector                           |
| Cache          | Redis                              |
| Workers        | Background worker system           |
| LLM            | Provider abstraction               |
| Voice          | STT + TTS / realtime voice         |
| Testing        | pytest                             |
| Linting        | Ruff                               |
| Type Checking  | mypy                               |
| Containers     | Docker                             |
| CI/CD          | Git-based CI/CD                    |
| Observability  | Structured logs + metrics + traces |

---

# 122. Why Python?

Python is suitable for:

* AI/LLM integration
* agent orchestration
* data processing
* web APIs
* automation
* research tooling
* machine learning ecosystem

It also has a mature ecosystem for AI applications.

---

# 123. Why FastAPI?

FastAPI provides:

* async support
* type-safe request handling
* automatic OpenAPI
* Pydantic integration
* good developer experience

It fits the API and orchestration layer well.

---

# 124. Why PostgreSQL?

PostgreSQL provides:

* relational integrity
* transactions
* indexing
* JSON support
* mature production ecosystem
* strong consistency

It should remain the company's primary source of truth.

---

# 125. Why Redis?

Redis is useful for:

* queues
* caching
* locks
* temporary state
* rate limiting

It should not replace PostgreSQL as permanent company state.

---

# 126. Why Next.js?

Next.js provides a strong foundation for:

* dashboard
* authentication UI
* server/client rendering
* routing
* real-time UI integration

---

# 127. Why Modular Agents?

Agents should be replaceable.

The company may eventually use:

```text
Model A
Model B
Model C
Custom Model
```

without changing organizational architecture.

---

# 128. Scalability Strategy

Start:

```text
One backend
One PostgreSQL
One Redis
A few workers
```

Scale later:

```text
API instances
Worker instances
Agent runtime workers
Task queues
Database replicas
Object storage
Dedicated services
```

---

# 129. Future Service Extraction

If scaling requires microservices, likely extraction boundaries are:

```text
Voice Service
Agent Runtime Service
Task Service
Tool Gateway Service
Notification Service
Document Service
Analytics Service
```

These should not be extracted until there is a real operational reason.

---

# 130. Reliability Strategy

The system must assume:

```text
LLMs fail
Tools fail
Networks fail
Workers fail
APIs fail
Users disconnect
```

Therefore:

* persist state
* use retries
* use timeouts
* use idempotency
* use recovery
* use audit logs
* make workflows resumable

---

# 131. Recovery Architecture

```text
Worker crashes
     ↓
Task remains IN_PROGRESS
     ↓
Recovery Scanner
     ↓
Detect stale task
     ↓
Determine safe recovery
     ↓
Resume / Retry / Reassign
```

---

# 132. Stale Task Detection

Tasks can include:

```text
heartbeat
last_activity_at
worker_id
execution_id
```

If a worker disappears, the task can be recovered.

---

# 133. Dead Letter Handling

Tasks that repeatedly fail should enter a dead-letter state.

```text
FAILED
 ↓
Retry 1
 ↓
Retry 2
 ↓
Retry 3
 ↓
DEAD_LETTER
 ↓
CEO / Human Review
```

---

# 134. Configuration Architecture

Configuration should be environment-based.

Example:

```text
APP_ENV
DATABASE_URL
REDIS_URL

LLM_PROVIDER
LLM_MODEL

VOICE_PROVIDER

MAX_AGENT_STEPS
MAX_TOOL_CALLS

APPROVAL_THRESHOLDS
```

Secrets should be injected securely.

---

# 135. Feature Configuration

Feature flags can control:

```text
voice_enabled
github_enabled
email_enabled
autonomous_execution_enabled
proactive_alerts_enabled
external_publishing_enabled
```

---

# 136. Development Workflow

Developer workflow:

```text
Issue
 ↓
Design
 ↓
Implementation
 ↓
Unit Tests
 ↓
Integration Tests
 ↓
PR
 ↓
Review
 ↓
CI
 ↓
Merge
 ↓
Deploy
```

AI coding agents must follow the same workflow.

---

# 137. AI Development Workflow

Coding agent:

```text
Task
 ↓
Inspect repository
 ↓
Understand architecture
 ↓
Plan
 ↓
Modify code
 ↓
Run tests
 ↓
Run lint/type checks
 ↓
Review diff
 ↓
Create PR
```

AI should not blindly rewrite large portions of the repository.

---

# 138. Database Migration Workflow

Schema changes:

```text
Modify Model
 ↓
Create Migration
 ↓
Review Migration
 ↓
Run Tests
 ↓
Apply Staging Migration
 ↓
Verify
 ↓
Production Migration
```

Migrations should be version controlled.

---

# 139. Documentation Architecture

The repository should maintain:

```text
PRD.md
    ↓
What / Why

ARCHITECTURE.md
    ↓
System Design

RULES.md
    ↓
Engineering Rules

API.md
    ↓
API Contracts

DATABASE.md
    ↓
Data Model

AGENTS.md
    ↓
Agent System

TOOLS.md
    ↓
Tool System

SECURITY.md
    ↓
Security Model

DEPLOYMENT.md
    ↓
Infrastructure
```

---

# 140. Architectural Decision Records

Major architectural decisions should have ADRs.

Example:

```text
docs/adr/
├── 001-modular-monolith.md
├── 002-postgresql-source-of-truth.md
├── 003-agent-tool-gateway.md
├── 004-human-approval-system.md
└── 005-task-graph-architecture.md
```

---

# 141. Architectural Anti-Patterns

Do not build:

### Giant CEO Prompt

```text
Everything
inside
one
prompt
```

### Disconnected Chatbots

```text
CEO chatbot
CMO chatbot
CTO chatbot
```

with no shared company state.

### Direct Tool Access

```text
Agent → API
```

without policy enforcement.

### LLM Security

```text
"AI says it is allowed."
```

### In-Memory Company State

```text
LLM conversation = database
```

### Unbounded Agent Loops

```text
while true:
    ask_model()
```

---

# 142. Recommended Initial Build Order

## Phase 1 — Foundation

Build:

```text
Repository
FastAPI
PostgreSQL
SQLAlchemy
Alembic
Authentication
Basic Next.js UI
```

---

## Phase 2 — Company Model

Build:

```text
Company
Department
Agent
Project
Task
```

---

## Phase 3 — CEO

Build:

```text
CEO Agent
Context Retrieval
Planner
Task Graph
Delegation
```

---

## Phase 4 — Agent Runtime

Build:

```text
Agent Registry
Agent Loader
Prompt Builder
LLM Gateway
Structured Outputs
Execution Loop
```

---

## Phase 5 — Tool Gateway

Build:

```text
Tool Registry
Permissions
Risk Classification
Approval System
Audit
```

---

## Phase 6 — First Tools

Implement:

```text
Web
Documents
GitHub
```

---

## Phase 7 — Workers

Implement:

```text
Queue
Workers
Retries
Recovery
Scheduling
```

---

## Phase 8 — Voice

Implement:

```text
STT
Conversation
CEO
TTS
Streaming
```

---

## Phase 9 — Dashboard

Implement:

```text
Company
Agents
Projects
Tasks
Approvals
Activity
```

---

## Phase 10 — Hardening

Implement:

```text
Security
Observability
Cost Tracking
AI Evaluations
Prompt Injection Testing
Load Testing
Recovery Testing
```

---

# 143. First End-to-End Milestone

The first complete vertical slice should be:

```text
User
 ↓
Text Request
 ↓
CEO
 ↓
Planner
 ↓
Task Graph
 ↓
Marketing Strategist
 ↓
Web Search
 ↓
Research Artifact
 ↓
Verification
 ↓
CEO
 ↓
Final Report
```

Do not wait until every department is implemented.

One complete workflow is more valuable than many disconnected components.

---

# 144. Second Vertical Slice

Then implement:

```text
User
 ↓
CEO
 ↓
CTO
 ↓
Software Engineer
 ↓
GitHub
 ↓
Code Change
 ↓
Tests
 ↓
Pull Request
 ↓
Verification
 ↓
CEO
```

---

# 145. Third Vertical Slice

Then:

```text
User
 ↓
CEO
 ↓
Sales
 ↓
Customer Data
 ↓
Analysis
 ↓
Report
 ↓
Approval
 ↓
External Action
```

This validates the approval architecture.

---

# 146. Final Architecture

The complete system can be summarized as:

```text
                              USER
                                │
                     ┌──────────┴──────────┐
                     │                     │
                   VOICE                  WEB
                     │                     │
                     └──────────┬──────────┘
                                ▼
                       EXPERIENCE LAYER
                                │
                                ▼
                           API GATEWAY
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
             Conversation              Company API
                    │
                    ▼
               CEO AGENT
                    │
          ┌─────────┼─────────┐
          │         │         │
          ▼         ▼         ▼
       Planner   Context    Policies
          │      Retrieval      │
          └─────────┬───────────┘
                    ▼
               TASK ENGINE
                    │
             ┌──────┼──────┐
             ▼      ▼      ▼
            CTO    CMO    SALES
             │      │      │
             ▼      ▼      ▼
        SPECIALIST AGENTS
             │      │      │
             └──────┼──────┘
                    ▼
               AGENT RUNTIME
                    │
                    ▼
                 LLM GATEWAY
                    │
                    ▼
              STRUCTURED OUTPUT
                    │
                    ▼
               TOOL GATEWAY
                    │
               POLICY ENGINE
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
         WEB      GITHUB     EMAIL
          │         │         │
          └─────────┼─────────┘
                    ▼
               VERIFICATION
                    │
                    ▼
              COMPANY STATE
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
      PostgreSQL  Redis    pgvector
          │
          ▼
      AUDIT / EVENTS
          │
          ▼
       DASHBOARD
          │
          ▼
         USER
```

---

# 147. Core Architecture Rules

The architecture is built around these rules:

1. **The user communicates primarily with the CEO.**
2. **The CEO orchestrates rather than doing every task itself.**
3. **Department heads manage specialists.**
4. **Agents operate within explicit authority boundaries.**
5. **All important company state is persisted.**
6. **PostgreSQL is the authoritative structured state.**
7. **Vector search is for retrieval, not authority.**
8. **Redis is for temporary operational state.**
9. **All external tools go through the Tool Gateway.**
10. **Permissions are enforced by deterministic software.**
11. **Consequential actions may require human approval.**
12. **Agent output is validated before execution.**
13. **Important results are verified before completion.**
14. **Long-running work runs asynchronously.**
15. **Tasks are persistent and recoverable.**
16. **Retries are bounded.**
17. **Agent loops are bounded.**
18. **Delegation depth is bounded.**
19. **Task graphs cannot contain cycles.**
20. **External content is untrusted.**
21. **Secrets never enter prompts unnecessarily.**
22. **Production access is restricted.**
23. **Every consequential external action is auditable.**
24. **The system can stop agents and workflows.**
25. **Human authority remains above autonomous execution.**

---

# 148. Architecture North Star

The system should ultimately behave like a real operating organization:

```text
                         FOUNDER
                            │
                            ▼
                           CEO
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
            CTO            CMO           SALES
             │              │              │
       Engineering      Marketing         Sales
             │              │              │
             └──────────────┼──────────────┘
                            │
                            ▼
                     OPERATING SYSTEM
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
           TASKS          TOOLS          MEMORY
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                         RESULTS
                            │
                            ▼
                        VERIFICATION
                            │
                            ▼
                           CEO
                            │
                            ▼
                         FOUNDER
```

The key architectural objective is not simply to create powerful AI agents.

It is to create a **reliable system that coordinates AI agents into a coherent company**.

The final system should therefore optimize for:

```text
                    RELIABILITY
                         ▲
                         │
            SECURITY ────┼──── VERIFICATION
                         │
                         │
          HUMAN CONTROL ─┼─ PERSISTENCE
                         │
                         ▼
                  AUTONOMOUS EXECUTION
```

The AI provides reasoning and execution capability.

The architecture provides:

**state + organization + permissions + tools + persistence + verification + recovery + observability.**

Together, these components form the AI Company OS.
