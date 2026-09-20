# MEMORY.md

# AI Company OS — Memory & Work State Architecture

This document defines:

* what the company remembers
* where that information lives
* what is authoritative
* how current state differs from history
* how agents retrieve context
* how work, files, errors, approvals, and decisions remain traceable
* how memory evolves from basic operational state into advanced company knowledge

This document defines the **memory and state architecture**.

It does not replace:

* `RULES.md` — engineering, security, reliability, and behavioral rules
* `PHASES.md` — development order and project roadmap

---

# 1. Core Principle

## LLM Context Is Not Company Memory

An LLM's context window is temporary.

The company must not depend on an agent remembering something because it appeared in a previous conversation.

The system must persist important information externally.

```text
LLM Context
    ↓
Temporary reasoning context

Company Memory
    ↓
Persistent system state
```

The company must survive:

* agent replacement
* model replacement
* server restart
* conversation restart
* context-window loss
* failed agent runs
* task retries
* deployment
* scaling
* organizational changes

The company remembers independently of any individual model.

---

# 2. Memory Has Multiple Layers

"Memory" is not one database.

The system contains several different forms of state.

```text
                    COMPANY MEMORY
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
 Operational          Execution          Historical
   State               State              History
        │                 │                 │
        ▼                 ▼                 ▼
 PostgreSQL          Runtime State       Activities
 Tasks               Agent Runs          Audit Logs
 Projects            Presence            Events
 Agents              Tool Runs           Decisions
        │
        ├──────────────────────────────┐
        │                              │
        ▼                              ▼
    Artifacts                    Knowledge
 Documents                      Research
 Files                           Decisions
 Reports                         Procedures
 Code                            Semantic Retrieval
```

There is also short-lived runtime infrastructure:

```text
Redis
├── queues
├── locks
├── temporary state
├── caching
└── realtime coordination
```

Redis is not permanent company memory.

---

# 3. Source of Truth

| Information              | Primary Source of Truth                                    |
| ------------------------ | ---------------------------------------------------------- |
| Users                    | PostgreSQL                                                 |
| Companies                | PostgreSQL                                                 |
| Departments              | PostgreSQL                                                 |
| Agents                   | PostgreSQL + agent definitions                             |
| Projects                 | PostgreSQL                                                 |
| Tasks                    | PostgreSQL                                                 |
| Dependencies             | PostgreSQL                                                 |
| Assignments              | PostgreSQL                                                 |
| Approvals                | PostgreSQL                                                 |
| Errors                   | PostgreSQL                                                 |
| Agent runs               | PostgreSQL                                                 |
| Presence                 | PostgreSQL/runtime state                                   |
| Activity history         | PostgreSQL                                                 |
| Audit history            | Durable audit storage                                      |
| Files                    | Repository/filesystem/object storage + PostgreSQL metadata |
| Commits                  | Git                                                        |
| Pull requests            | Git provider                                               |
| Documents                | Document/object storage + PostgreSQL metadata              |
| Structured company state | PostgreSQL                                                 |
| Semantic retrieval       | PostgreSQL + pgvector                                      |
| Temporary queues         | Redis                                                      |
| Temporary locks          | Redis                                                      |
| Realtime delivery        | Event/outbox infrastructure                                |
| LLM context              | Temporary/generated                                        |

No cache, vector index, prompt, or LLM context may become the authoritative source of company state.

---

# 4. Memory Design Goals

Company memory must be:

* persistent
* queryable
* attributable
* timestamped
* evidence-backed
* permission-aware
* recoverable
* auditable
* company-scoped
* project-aware
* agent-independent
* model-independent
* resistant to hallucinated state
* capable of distinguishing current state from historical state

The system should also know when information is:

```text
KNOWN
INFERRED
ESTIMATED
UNKNOWN
STALE
```

The CEO must never present an inference as an authoritative fact.

---

# 5. Implementation Philosophy

Do not build the entire memory platform at the beginning.

Memory evolves with the company system.

```text
Company
   ↓
Projects
   ↓
Tasks
   ↓
Assignments
   ↓
Agent Execution
   ↓
Basic Company State
   ↓
Kanban
   ↓
Activity History
   ↓
Agent Presence
   ↓
Error Tracking
   ↓
File / Code Tracking
   ↓
Realtime Operations
   ↓
Artifacts
   ↓
Advanced Knowledge
   ↓
Semantic / Vector Memory
   ↓
Advanced Agent Memory
```

The system should first remember **what the company is doing**.

Later it can remember **what the company knows**.

---

# 6. What NOT to Build Early

Do not begin with:

* a giant vector database
* complex memory graphs
* autonomous long-term learning
* automatic agent personality learning
* enterprise knowledge graphs
* dozens of specialized memory stores
* complex event infrastructure
* microservices everywhere
* 50+ agents
* sophisticated semantic retrieval
* automatic policy learning from agent experience

These are later capabilities.

The first objective is reliable operational state.

---

# 7. Core Company Entities

The core entities are:

```text
User
Company
Department
Agent
Project
Task
Task Dependency
Task Assignment
Project Member
Agent Run
Agent Presence
Activity
Audit Event
Approval
Error
Artifact
Repository
Branch
Commit
Pull Request
File Work
```

Later:

```text
Document
Decision
Knowledge Item
Customer
Conversation
Procedure
Agent Memory
Knowledge Chunk
Embedding
```

---

# 8. Company Hierarchy

The company structure is persistent state.

```text
Company
│
├── Departments
│
├── Agents
│
├── Projects
│
├── Policies
│
└── Company Knowledge
```

Agents belong to departments.

Agents may participate in projects without becoming permanently owned by the project.

Historical records must remain understandable even if:

* an agent is renamed
* an agent is disabled
* an agent is replaced
* a department changes
* a project is archived

Historical records should therefore preserve the actor identity and, where useful, a display-name snapshot.

---

# 9. Actor Model

Any important action should identify who or what performed it.

Actors can be:

```text
USER
AGENT
SYSTEM
WORKER
INTEGRATION
```

Important records should include fields such as:

```text
actor_id
actor_type
created_at
updated_at
company_id
```

This allows the system to answer:

> Who did this?

rather than only:

> What happened?

---

# 10. Company Scoping

Every company-owned record must be scoped to a company.

At minimum, important entities should carry:

```text
company_id
```

This includes:

* projects
* tasks
* assignments
* activities
* errors
* approvals
* artifacts
* agent runs
* files
* documents
* knowledge

Memory retrieval must respect company boundaries.

An agent must never retrieve another company's information merely because a semantic search happens to match it.

---

# 11. Projects

Projects represent meaningful company objectives.

Example:

```text
Company
└── Germany AI Launch
```

A project contains:

* objective
* description
* owner
* status
* priority
* deadline
* team
* tasks
* dependencies
* artifacts
* decisions
* activity
* blockers
* results

Projects are persistent.

When a project is completed, it becomes historical company knowledge rather than disappearing.

---

# 12. Project Team

A project may contain:

```text
Project
├── Owner
├── Contributors
├── Reviewers
├── Verifiers
└── Approvers
```

Project membership should be separate from individual task assignment.

An agent can:

* belong to a project
* own a task
* contribute to a task
* review another agent's work
* verify a result
* approve an action

These are different responsibilities.

---

# 13. Tasks

Tasks represent executable work.

A task should contain at least:

```text
id
company_id
project_id
parent_task_id
title
objective
description
created_by
assigned_to
status
priority
dependencies
deadline
required_tools
approval_requirement
input_context
output
artifacts
created_at
started_at
completed_at
```

Optional future hierarchy:

```text
Objective
   ↓
Project
   ↓
Epic
   ↓
Task
   ↓
Subtask
   ↓
Agent Run
   ↓
Tool Execution
```

Do not require epics if the project does not need them.

---

# 14. Task State

Task state must be explicit.

Recommended states:

```text
CREATED
PLANNED
READY
ASSIGNED
IN_PROGRESS
WAITING
BLOCKED
VERIFYING
COMPLETED
VERIFIED
FAILED
CANCELLED
APPROVAL_REQUIRED
```

State semantics must be documented and enforced by the application.

Important distinction:

```text
COMPLETED
    ↓
Agent says execution is finished

VERIFIED
    ↓
Required evidence/checks passed

CLOSED
    ↓
Optional future business lifecycle state
```

Do not use "completed" and "verified" interchangeably.

Approval should preferably be represented as an approval record/gate rather than creating an unnecessarily large state machine.

---

# 15. Progress

Progress must be evidence-backed.

Do not allow an LLM to invent:

```text
"Task is 83% complete."
```

unless the system has a defined basis for that number.

Progress may be derived from:

* completed subtasks
* completed workflow steps
* explicit agent reports
* verified milestones

Example:

```text
Task
├── Research       ✓
├── Analysis       ✓
├── Draft          ✓
└── Verification   pending
```

This can produce meaningful progress without fake precision.

---

# 16. Task Dependencies

Tasks may depend on other tasks.

Example:

```text
Market Research
      ↓
Financial Analysis
      ↓
Launch Decision
      ↓
Launch Plan
```

Dependencies must be acyclic.

The system must detect:

* circular dependencies
* invalid dependencies
* completed dependency failures
* blocked chains

---

# 17. Ownership and Assignment

Task ownership is not the same as task history.

A task may have:

```text
Current Owner
Contributors
Reviewer
Verifier
Approver
Assignment History
```

Assignment history must be preserved.

Example:

```text
Task T001

Assigned:
CMO
    ↓
Marketing Strategist
    ↓
Copywriter

Final owner:
Copywriter

Historical assignments:
CMO
Marketing Strategist
Copywriter
```

This allows the CEO to answer:

> Who worked on this?

without guessing from current ownership.

---

# 18. Delegation History

Delegation is a first-class historical record.

Example:

```text
CEO
 ↓
CMO
 ↓
Marketing Strategist
 ↓
SEO Specialist
```

The system should record:

```text
delegated_by
delegated_to
task_id
reason
timestamp
result
```

This makes the organizational execution chain visible.

---

# 19. Agent Runs

An agent run is an execution instance.

It is not the same thing as a task.

```text
Task
   ↓
Agent Run
   ↓
Tool Calls
   ↓
Artifacts
   ↓
Result
```

A single task may have multiple runs because of:

* retries
* failures
* reassignment
* verification
* recovery
* model changes

Example:

```text
Task T001

Run 1 → failed
Run 2 → completed
Run 3 → verification
```

Agent runs should record:

```text
run_id
task_id
agent_id
started_at
ended_at
status
current_step
model
prompt_version
result
error
tool_calls
```

Execution telemetry is useful memory, but it is not itself the authoritative task state.

---

# 20. Agent Presence

Presence answers:

> What is this agent doing right now?

Recommended states:

```text
ONLINE
IDLE
WORKING
WAITING
BLOCKED
ERROR
OFFLINE
```

Presence is operational state, not permanent history.

It should be based on:

* heartbeat
* active run
* current task
* current step
* last activity
* runtime state

Example:

```text
Agent:
Backend Engineer

Presence:
WORKING

Task:
Implement authentication API

Current step:
Writing integration tests

Last heartbeat:
12 seconds ago
```

Presence must be stale-aware.

If an agent stops reporting, the system must not assume it is still working.

---

# 21. Current Work Context

For every active agent, the company should eventually be able to answer:

```text
Who?
What?
Why?
Where?
Since when?
Current step?
Blocked by?
Last update?
```

Example:

```text
Agent: CMO

Project:
Germany AI Launch

Task:
Analyze German AI market

Current step:
Competitor research

Started:
09:42

Blocked:
No

Last update:
09:58
```

This is an operational view derived from persisted state.

---

# 22. Activities

Activities answer:

> What happened?

Examples:

```text
CEO created project
CEO assigned task
CMO started research
Sales completed analysis
Finance requested approval
CTO committed code
Task became blocked
Agent failed
Task was verified
```

Activities are human-readable company history.

Each activity should contain:

```text
id
company_id
actor
type
entity_type
entity_id
message/data
created_at
correlation_id
```

Activities should be append-oriented and should not silently disappear.

---

# 23. Audit Logs

Activity history and audit logs are different.

### Activity

Human-readable operational history.

Example:

```text
"CTO completed authentication task."
```

### Audit

Technical/security record.

Example:

```text
actor=agent_123
action=tool.execute
tool=github.commit
target=repo_42
timestamp=...
request_id=...
result=...
```

The audit layer should support investigation and accountability.

---

# 24. Events and Idempotency

Important events should have stable identifiers.

Examples:

```text
event_id
correlation_id
causation_id
idempotency_key
```

This prevents duplicated activity when workers retry.

Example:

```text
Agent completes task
        ↓
Database transaction
        ↓
Outbox event
        ↓
Realtime delivery
```

The same event should not accidentally produce five duplicate activity records because a worker retried.

---

# 25. Errors

Errors are part of company memory.

An error should not disappear into logs.

Example:

```text
Error
├── detected_by
├── task
├── project
├── agent
├── assigned_to
├── severity
├── status
├── root_cause
├── evidence
├── resolution
├── resolved_by
├── verified_by
└── timestamps
```

Error lifecycle:

```text
DETECTED
   ↓
TRIAGED
   ↓
ASSIGNED
   ↓
INVESTIGATING
   ↓
FIXED
   ↓
VERIFYING
   ↓
RESOLVED
```

An error is not resolved merely because an agent claims it is fixed.

Verification evidence is required.

---

# 26. Blockers

A blocker is different from an error.

Examples:

```text
WAITING_FOR_APPROVAL
WAITING_FOR_USER
WAITING_FOR_DEPENDENCY
WAITING_FOR_TOOL
WAITING_FOR_INFORMATION
EXTERNAL_BLOCKER
```

The CEO should be able to query:

> What is blocking the company?

The system should identify:

* blocked tasks
* blocking tasks
* blocked agents
* blocked projects
* blocked dependencies
* required human decisions

---

# 27. Engineering Memory

Engineering work requires traceability.

The system should eventually connect:

```text
Task
 ↓
Agent
 ↓
File
 ↓
Branch
 ↓
Commit
 ↓
Pull Request
 ↓
Verification
```

Example:

```text
Task T042
   ↓
Backend Engineer
   ↓
auth/service.py
   ↓
feature/auth
   ↓
commit abc123
   ↓
PR #18
   ↓
QA verification
```

This allows the CEO to answer:

> What changed because of this task?

---

# 28. File Work

A file should not permanently belong to an agent.

Instead, track temporary work relationships.

Example:

```text
file_work

file
agent
task
branch
started_at
ended_at
status
```

A file can therefore have:

```text
Current work
Historical work
Multiple contributors
Multiple tasks
```

This prevents false permanent ownership.

---

# 29. File Conflict Detection

Before allowing concurrent engineering work, the system should detect:

```text
Agent A → editing auth.py
Agent B → editing auth.py
```

The system can then:

* allow it
* warn
* coordinate
* serialize work
* require review

The policy belongs to the engineering workflow, not to the LLM.

---

# 30. Repositories, Branches, Commits, and PRs

These should remain linked to tasks where possible.

Example:

```text
Repository
   ↓
Branch
   ↓
Commit
   ↓
Pull Request
   ↓
Task
```

Git remains authoritative for Git state.

PostgreSQL stores the company's relationship to that Git state.

---

# 31. Artifacts

Artifacts are outputs produced by work.

Examples:

```text
Report
Document
Spreadsheet
Image
Code Patch
Research
Analysis
Presentation
Dataset
Specification
```

An artifact should contain metadata such as:

```text
artifact_id
company_id
project_id
task_id
created_by
artifact_type
location
version
created_at
```

The actual file may live in:

* object storage
* filesystem
* document system
* Git
* external provider

PostgreSQL stores the relationship and metadata.

---

# 32. Knowledge vs Work Memory

These must remain separate.

### Work Memory

Answers:

> What is happening?

Examples:

```text
Task
Assignment
Agent Run
Presence
Error
Project Status
Approval
```

### Knowledge Memory

Answers:

> What does the company know?

Examples:

```text
Market research
Company strategy
Customer knowledge
Policies
Decisions
Procedures
Research findings
Lessons learned
```

Work memory should be operationally authoritative.

Knowledge memory can contain interpretation and retrieved information, provided provenance is maintained.

---

# 33. Decisions

Important company decisions should be persisted.

Example:

```text
Decision

Question:
Should we launch in Germany?

Decision:
Approved for pilot

Decided by:
User

Date:
...

Evidence:
Market research
Financial analysis
Technical analysis

Related project:
Germany AI Launch
```

A decision should preserve:

* question
* decision
* decision maker
* date
* rationale
* evidence
* related tasks/projects
* status

Historical decisions should not be silently rewritten.

If a decision changes:

```text
Decision A
    ↓ superseded by
Decision B
```

---

# 34. Provenance

Important information should answer:

> Where did this come from?

Possible sources:

```text
USER
AGENT
DATABASE
TOOL
DOCUMENT
EMAIL
GITHUB
WEB
SYSTEM
DERIVED
```

Example:

```text
Claim:
Enterprise pipeline = €2.4M

Source:
CRM

Observed:
2026-09-21

Confidence:
HIGH
```

A derived result should not pretend to be directly observed.

---

# 35. Freshness

Memory can become stale.

Important information should support:

```text
observed_at
updated_at
expires_at
freshness
```

Example:

```text
CRM pipeline:
Observed 4 minutes ago
Fresh

Market report:
Observed 8 months ago
Potentially stale
```

The CEO should consider freshness when answering current-state questions.

---

# 36. Confidence

Confidence should describe the evidence, not manufacture certainty.

Use:

```text
HIGH
MEDIUM
LOW
UNKNOWN
```

Combined with provenance:

```text
Known:
Direct database result

Inferred:
Derived from several records

Estimated:
Calculated using assumptions

Unknown:
Insufficient evidence
```

The CEO should say when something is unknown.

---

# 37. Memory Retrieval

The CEO should not load the entire company memory into every prompt.

Instead:

```text
User Request
     ↓
Intent
     ↓
Context Builder
     ↓
Relevant State
     ↓
Relevant History
     ↓
Relevant Knowledge
     ↓
Permissions
     ↓
LLM Context
```

The Context Builder determines what the CEO needs.

---

# 38. Context Builder

The Context Builder should retrieve only relevant information.

Example query:

> Why is Project X delayed?

Possible retrieval:

```text
Project X
Tasks
Blocked tasks
Dependencies
Errors
Agent runs
Recent activity
Approvals
Relevant decisions
Relevant artifacts
```

It should not retrieve unrelated:

```text
Marketing projects
Old customer records
Unrelated engineering tasks
Private company information
```

---

# 39. Retrieval Priority

A useful retrieval order is:

```text
1. Current authoritative state
2. Active tasks
3. Current blockers
4. Recent activity
5. Relevant execution history
6. Relevant artifacts
7. Relevant decisions
8. Relevant company knowledge
9. Semantic search
```

Semantic search should complement structured queries, not replace them.

---

# 40. PostgreSQL and pgvector

PostgreSQL is the primary structured data store.

Later, pgvector can provide semantic retrieval inside PostgreSQL.

This does not require a separate vector database.

Example:

```text
PostgreSQL
├── Tasks
├── Projects
├── Agents
├── Activities
├── Decisions
├── Documents
└── Knowledge chunks
        │
        └── embeddings
```

Vector search is a retrieval mechanism.

It is not the authoritative company state.

---

# 41. Agent Memory

Agent-specific memory may eventually contain:

```text
previous experiences
successful procedures
working preferences
specialized knowledge
task history
```

But agent memory must remain separate from company truth.

An agent's memory must never override:

* company policy
* database state
* permissions
* task state
* approval state
* security controls

If an agent is deleted, company memory must survive.

---

# 42. No Automatic Policy Learning

Agents must not silently convert their experiences into company policy.

For example:

```text
Agent discovered a useful workflow
```

does not mean:

```text
Company policy changed
```

A learned procedure should become an official company procedure only through an explicit workflow.

---

# 43. Memory Access Control

Not every agent should see every memory record.

Memory retrieval must respect:

```text
company
department
project
task
role
permission
data classification
```

Example:

```text
Sales Agent
    ↓
Sales data

CTO
    ↓
Engineering data

CEO
    ↓
Broader company information
    ↓
Still subject to policy
```

The CEO is not automatically exempt from security controls.

---

# 44. Sensitive Information

Sensitive information must be handled according to policy.

Examples:

```text
credentials
private customer data
financial information
legal information
personal information
security information
```

Sensitive data should have:

* access restrictions
* appropriate storage
* auditability
* minimization
* redaction where appropriate

Secrets must never be stored inside prompts or ordinary agent memory.

---

# 45. Retention and Archiving

Completed work should remain available.

Do not automatically delete:

```text
completed tasks
completed projects
historical assignments
important decisions
important artifacts
audit history
```

Instead use:

```text
ACTIVE
ARCHIVED
RETAINED
```

Retention rules may differ by data type.

For example:

```text
Current tasks → active
Completed tasks → retained
Old temporary runtime state → cleaned
Caches → disposable
Important audit records → durable
```

Archiving is not the same as deletion.

---

# 46. Current State vs History

The system should not reconstruct everything from events in the first version.

Maintain explicit current state:

```text
task.status
task.assigned_to
project.status
agent_presence.status
```

And maintain history:

```text
activity
audit
assignment history
agent runs
error events
```

Therefore:

```text
Current state
    +
Historical evidence
```

This makes queries simple and reliable.

Event sourcing can be considered later if there is a strong reason.

---

# 47. Realtime Architecture

Realtime information must not make the event stream the source of truth.

Preferred architecture:

```text
Agent / User
     ↓
Application Service
     ↓
PostgreSQL Transaction
     ↓
Outbox Event
     ↓
Realtime Worker
     ↓
SSE / WebSocket
     ↓
Dashboard
```

The database remains authoritative.

The realtime layer distributes changes.

If the realtime system fails:

```text
Company state remains safe.
```

When it recovers:

```text
Current state can be reloaded.
```

---

# 48. Operational Dashboard

The company operations screen should eventually show:

```text
COMPANY STATUS

Projects
Tasks
Blocked Work
Approvals
Errors

AGENTS

Who is online
Who is working
What they are doing
Current tasks
Current steps

WORK

Kanban
Recent activity
Project progress
Task ownership

ENGINEERING

Files
Branches
Commits
Pull Requests

HISTORY

Activity
Decisions
Artifacts
Errors
```

This is a read model over company state.

It is not a second source of truth.

---

# 49. Kanban

Kanban is a visualization of tasks.

Do not create a separate task database for Kanban.

Example:

```text
READY
   ↓
IN_PROGRESS
   ↓
WAITING
   ↓
VERIFYING
   ↓
VERIFIED
```

The Kanban board reads from task state.

Filters may include:

```text
Project
Department
Agent
Priority
Status
Deadline
Blocked
Error
```

---

# 50. CEO Queries

The memory system should eventually support questions such as:

### Current State

> What is happening right now?

### Work

> What is everyone working on?

### Project

> How is the Germany launch going?

### Blockers

> What is blocking us?

### Errors

> What went wrong today?

### Ownership

> Who worked on this task?

### History

> What happened yesterday?

### Decisions

> Why did we choose this strategy?

### Engineering

> What changed in the code?

### Accountability

> Who completed this?

### Verification

> Has this actually been verified?

### Knowledge

> What do we know about the German market?

### Attention

> What needs my attention?

These queries should be answered from appropriate sources rather than one generic memory search.

---

# 51. Canonical Query Strategy

For every CEO question:

```text
1. Identify intent
2. Identify relevant entities
3. Retrieve authoritative current state
4. Retrieve relevant history
5. Retrieve supporting evidence
6. Check permissions
7. Check freshness
8. Distinguish fact from inference
9. Generate response
```

Example:

```text
"What needs my attention?"

→ blocked tasks
→ pending approvals
→ critical errors
→ overdue tasks
→ failed runs
→ unresolved conflicts
→ important decisions
```

---

# 52. Memory and Verification

Memory must not become a place where unverified claims become facts.

Bad:

```text
Agent:
"I fixed the bug."

Database:
task.status = VERIFIED
```

Correct:

```text
Agent:
"I fixed the bug."

System:
record result

Verification:
run tests
inspect commit
check expected behavior

Then:

VERIFIED
```

Evidence should be stored or linked where practical.

---

# 53. Memory Consistency

Important state changes should happen transactionally where possible.

Example:

```text
Task completed
+
Assignment updated
+
Activity created
+
Outbox event created
```

These should be coordinated so the system does not end up with:

```text
Task = completed
Activity = missing
```

or:

```text
Task = in_progress
Dashboard = completed
```

The database is the authority.

---

# 54. Concurrency

Multiple agents may attempt to modify the same state.

The system must handle:

* concurrent task updates
* duplicate completion
* simultaneous assignment
* file conflicts
* repeated tool calls
* worker retries
* stale agent runs

Use:

* transactions
* row locking where appropriate
* optimistic concurrency where appropriate
* idempotency
* version fields where useful

Do not rely on the LLM to coordinate concurrency.

---

# 55. Memory Failure Behavior

If memory is unavailable:

```text
DO NOT GUESS
```

The agent should:

```text
pause
report missing state
retry if safe
escalate if necessary
```

Example:

```text
CEO:
"I can't verify the current project status because the company state store is unavailable."
```

That is preferable to inventing a status.

---

# 56. Memory and Agent Replacement

The company should continue functioning if:

```text
CEO model changes
CTO agent changes
Agent prompt changes
Agent implementation changes
LLM provider changes
```

Persistent company state belongs to the platform.

Agents consume and update that state.

Agents do not own the company's memory.

---

# 57. Basic Database Model

Initial core tables:

```text
users
companies
departments
agents

projects
project_members

tasks
task_dependencies
task_assignments

agent_runs
agent_presence

activities
audit_logs

approvals

errors
error_events

artifacts

repositories
branches
commits
pull_requests
file_work

outbox_events
```

Later:

```text
documents
decisions
knowledge_items
knowledge_chunks
agent_memory
customers
conversations
procedures
```

Avoid creating dozens of generic "memory" tables without a clear semantic purpose.

---

# 58. Suggested Core Relationships

```text
Company
│
├── Departments
│    └── Agents
│
├── Projects
│    ├── Project Members
│    ├── Tasks
│    │    ├── Dependencies
│    │    ├── Assignments
│    │    ├── Agent Runs
│    │    ├── Errors
│    │    └── Artifacts
│    │
│    └── Decisions
│
├── Activities
├── Audit Logs
├── Approvals
├── Repositories
└── Knowledge
```

---

# 59. Development Order

Memory development follows `PHASES.md`.

## Early phases

### Phase 3 — Company & Organization

Persist:

```text
companies
departments
agents
```

### Phase 4 — Agent Registry

Persist:

```text
agent definitions
hierarchy
capabilities
```

### Phase 5 — CEO Foundation

Begin reading/writing company state.

### Phase 6 — Projects & Basic Tasks

Persist:

```text
projects
tasks
dependencies
```

### Phase 7 — Task Assignment & Delegation

Persist:

```text
assignments
project membership
delegation history
```

### Phase 8 — Agent Runtime

Persist:

```text
agent runs
execution results
tool execution relationships
```

### Phase 9 — Tool Gateway

Persist:

```text
tool execution records
evidence
external references
```

### Phase 10 — Basic Approvals

Persist:

```text
approval requests
approval decisions
approvers
timestamps
```

### Phase 11 — Basic Memory & Company State

Formalize:

```text
company state
context retrieval
historical activity
basic knowledge
memory access
```

---

# 60. Later Memory Development

### Phase 12 — Kanban

Tasks become visually manageable.

### Phase 13 — Activity History

Create the persistent human-readable company timeline.

### Phase 14 — Agent Presence

Show:

```text
who is online
who is working
what they are doing
```

### Phase 15 — Error & Bug Management

Track:

```text
detection
ownership
investigation
resolution
verification
```

### Phase 16 — Engineering File Tracking

Connect:

```text
task
agent
file
branch
commit
PR
verification
```

### Phase 17 — Real-Time Operations

Add:

```text
outbox
event delivery
SSE/WebSocket
live dashboard
```

### Phase 18 — Documents & Artifacts

Formalize durable outputs.

### Phase 19 — Advanced Company Knowledge

Add:

```text
decisions
research
procedures
historical knowledge
```

### Phase 20 — Semantic / Vector Memory

Add:

```text
embeddings
semantic retrieval
hybrid search
```

### Phase 21 — Voice Interface

Allow voice to query and control company state.

### Phase 22 — Verification & Evaluation

Measure:

```text
retrieval quality
agent accuracy
task completion
verification quality
hallucination rate
```

### Phase 23+

Security hardening, observability, automation, deployment, autonomous workflows, and advanced intelligence.

---

# 61. Memory Architecture Over Time

The complete evolution should look like:

```text
PHASE 3
Company State
    ↓
PHASE 6
Projects + Tasks
    ↓
PHASE 7
Assignments + Delegation
    ↓
PHASE 8
Agent Runs
    ↓
PHASE 10
Approvals
    ↓
PHASE 11
Basic Memory
    ↓
PHASE 12
Kanban
    ↓
PHASE 13
Activity History
    ↓
PHASE 14
Agent Presence
    ↓
PHASE 15
Errors
    ↓
PHASE 16
File Tracking
    ↓
PHASE 17
Realtime
    ↓
PHASE 18
Artifacts
    ↓
PHASE 19
Advanced Knowledge
    ↓
PHASE 20
Semantic Memory
    ↓
PHASE 21
Voice
    ↓
PHASE 22+
Evaluation + Automation + Intelligence
```

---

# 62. Memory Rules

## Rule 1

LLM context is temporary.

## Rule 2

Company state is external and persistent.

## Rule 3

PostgreSQL is the source of truth for structured company state.

## Rule 4

Redis is not permanent company memory.

## Rule 5

Vector search is retrieval, not truth.

## Rule 6

Git remains authoritative for Git state.

## Rule 7

External systems remain authoritative for their own external data where applicable.

## Rule 8

Every important action has an actor.

## Rule 9

Important history must be preserved.

## Rule 10

Current state and historical state are different concepts.

## Rule 11

Agent memory must never override company state.

## Rule 12

Agents must not invent company state.

## Rule 13

Important claims should have provenance.

## Rule 14

Important claims should have freshness information when relevant.

## Rule 15

Unknown information must remain unknown.

## Rule 16

Inference must be distinguishable from fact.

## Rule 17

Completed work should remain historically queryable.

## Rule 18

Verification requires evidence.

## Rule 19

Kanban is a view of tasks, not another task database.

## Rule 20

Realtime delivery is not the source of truth.

## Rule 21

Activities and audit logs serve different purposes.

## Rule 22

Presence must be stale-aware.

## Rule 23

File work is temporary collaboration state, not permanent file ownership.

## Rule 24

Memory retrieval must respect permissions.

## Rule 25

Company memory must survive agent replacement.

## Rule 26

Sensitive data must follow access and retention policies.

## Rule 27

Automatic agent learning must never silently change company policy.

## Rule 28

Memory systems should be introduced only when their underlying workflow exists.

## Rule 29

Prefer simple persistent state before advanced semantic memory.

## Rule 30

When memory is unavailable, pause or escalate rather than guess.

---

# 63. Final Architecture

The complete company memory model is:

```text
                         USER
                          │
                          ▼
                     CEO AGENT
                          │
                          ▼
                   CONTEXT BUILDER
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   Current State       History          Knowledge
        │                 │                 │
        ▼                 ▼                 ▼
   PostgreSQL          Activity         Documents
   Projects            Audit            Decisions
   Tasks               Runs             Research
   Agents              Errors           Procedures
   Approvals           Events           pgvector
        │
        ▼
   AGENT RUNTIME
        │
        ├───────────────┐
        ▼               ▼
     Tools           Artifacts
        │               │
        ▼               ▼
 External Systems    File/Object Storage
        │
        ▼
   Verified Evidence
        │
        ▼
   PostgreSQL State
        │
        ▼
   Outbox Events
        │
        ▼
 Realtime Gateway
        │
        ▼
   Company Dashboard
```

The fundamental architecture is therefore:

```text
STATE
  +
EXECUTION
  +
HISTORY
  +
EVIDENCE
  +
KNOWLEDGE
  +
RETRIEVAL
  +
REALTIME VIEWS
```

Not:

```text
One giant AI memory.
```

---

# 64. Final Goal

The company should eventually be able to answer:

```text
What is happening?

Who is working?

What is everyone working on?

Why are they working on it?

What has been completed?

What has been verified?

What is blocked?

What failed?

Who worked on it?

What changed?

Which files changed?

Which commits changed?

What decisions were made?

Why were they made?

What does the company know?

What needs my attention?

What happened previously?

What should happen next?
```

And it should answer these questions using persistent, permission-aware, evidence-backed company state.

The long-term objective is:

```text
BUILD THE COMPANY
        ↓
BUILD THE WORK
        ↓
BUILD THE EXECUTION
        ↓
MAKE THE WORK VISIBLE
        ↓
MAKE THE HISTORY PERSISTENT
        ↓
MAKE THE SYSTEM REAL-TIME
        ↓
MAKE THE COMPANY REMEMBER
        ↓
MAKE THE COMPANY KNOW
        ↓
MAKE THE COMPANY INTELLIGENT
        ↓
MAKE THE COMPANY MORE AUTONOMOUS
```

The company should become increasingly capable without becoming dependent on any single model, agent, prompt, conversation, or runtime.
