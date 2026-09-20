# AI Company OS — Design System

## 1. Design Philosophy

The AI Company OS is a **company control center powered by AI agents**.

The interface must communicate:

* Intelligence
* Trust
* Control
* Clarity
* Professionalism
* Speed
* Transparency
* Human authority
* Operational visibility

The product should **not** look like:

* A generic chatbot
* A gaming interface
* A futuristic sci-fi dashboard
* A social media application
* An overly colorful SaaS template
* A collection of disconnected AI chat windows

The product should feel like:

> **A modern executive operating system where a human can see, control, and direct an AI-powered company.**

The CEO agent is the central interaction point, but the UI must make it clear that the CEO is coordinating a larger organization.

---

# 2. Core Design Principles

## 2.1 Clarity Over Decoration

Every visual element should help the user understand:

* What is happening?
* Who is doing it?
* Why is it happening?
* What is waiting?
* What needs approval?
* What has completed?
* What requires attention?

Avoid decorative UI that does not provide operational value.

---

## 2.2 Information Hierarchy

The most important information should always be visually dominant.

Priority:

```text
1. Critical alerts / approvals
2. Current company status
3. Active work
4. CEO activity
5. Agent activity
6. Metrics
7. Historical information
8. Secondary metadata
```

---

## 2.3 Human Control Must Be Visible

The interface should clearly communicate when the system:

* Is planning
* Is executing
* Is waiting
* Needs approval
* Is blocked
* Has completed work
* Failed
* Requires human intervention

The user should never wonder:

> "Did the AI actually do that?"

The UI should provide evidence and status.

---

## 2.4 Calm Intelligence

The design should feel intelligent without being visually noisy.

Use:

* Strong typography
* Generous spacing
* Subtle borders
* Restrained colors
* Clear status indicators
* Minimal animation
* High-quality data visualization

Avoid:

* Excessive gradients
* Excessive glow effects
* Constant animations
* Giant colorful cards
* Neon interfaces
* Excessive rounded containers

---

# 3. Visual Direction

## Primary Style

Recommended visual style:

```text
Modern
+
Minimal
+
Executive
+
Technical
+
AI-native
```

Reference mental model:

```text
Enterprise OS
       +
Developer Platform
       +
Executive Dashboard
       +
AI Agent Control Center
```

The UI should sit visually between a high-end enterprise product and a modern developer tool.

---

# 4. Color and Theme

The application should support both:

* Dark theme
* Light theme

Dark theme should be the primary/default experience for the main application.

---

# 5. Color Philosophy

Colors should communicate **meaning**, not decoration.

Recommended semantic system:

| Purpose     | Color         |
| ----------- | ------------- |
| Primary     | Indigo / Blue |
| Secondary   | Violet        |
| Success     | Green         |
| Warning     | Amber         |
| Error       | Red           |
| Information | Cyan / Blue   |
| Neutral     | Slate / Gray  |
| Pending     | Purple        |
| Approval    | Amber         |
| Blocked     | Red           |
| Running     | Blue          |
| Completed   | Green         |

Avoid assigning random colors to agents.

Agent colors should be consistent and meaningful.

---

# 6. Dark Theme

Recommended primary dark palette:

```text
Background:
#09090B

Surface:
#111113

Surface Elevated:
#18181B

Surface Strong:
#202023

Border:
#27272A

Border Strong:
#3F3F46

Primary Text:
#FAFAFA

Secondary Text:
#A1A1AA

Muted Text:
#71717A

Primary:
#6366F1

Primary Hover:
#818CF8

Secondary:
#8B5CF6

Success:
#22C55E

Warning:
#F59E0B

Error:
#EF4444

Info:
#06B6D4
```

The exact values may be adjusted during implementation, but the semantic relationships should remain.

---

# 7. Light Theme

Recommended light palette:

```text
Background:
#FAFAFA

Surface:
#FFFFFF

Surface Elevated:
#FFFFFF

Surface Strong:
#F4F4F5

Border:
#E4E4E7

Border Strong:
#D4D4D8

Primary Text:
#18181B

Secondary Text:
#52525B

Muted Text:
#71717A

Primary:
#4F46E5

Primary Hover:
#4338CA

Secondary:
#7C3AED

Success:
#16A34A

Warning:
#D97706

Error:
#DC2626

Info:
#0891B2
```

---

# 8. CSS Color Tokens

The frontend should not hard-code colors throughout components.

Use semantic design tokens.

Example:

```css
:root {
  --color-background: #fafafa;
  --color-surface: #ffffff;
  --color-surface-elevated: #ffffff;

  --color-border: #e4e4e7;
  --color-border-strong: #d4d4d8;

  --color-text-primary: #18181b;
  --color-text-secondary: #52525b;
  --color-text-muted: #71717a;

  --color-primary: #4f46e5;
  --color-primary-hover: #4338ca;

  --color-success: #16a34a;
  --color-warning: #d97706;
  --color-error: #dc2626;
  --color-info: #0891b2;
}

.dark {
  --color-background: #09090b;
  --color-surface: #111113;
  --color-surface-elevated: #18181b;

  --color-border: #27272a;
  --color-border-strong: #3f3f46;

  --color-text-primary: #fafafa;
  --color-text-secondary: #a1a1aa;
  --color-text-muted: #71717a;

  --color-primary: #6366f1;
  --color-primary-hover: #818cf8;

  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #06b6d4;
}
```

---

# 9. Status Colors

Status must be consistent throughout the entire application.

## Created

Neutral:

```text
Gray
```

## Planned

```text
Indigo
```

## Ready

```text
Blue
```

## Assigned

```text
Purple
```

## In Progress

```text
Blue
```

## Waiting

```text
Yellow / Amber
```

## Blocked

```text
Red
```

## Approval Required

```text
Amber
```

## Completed

```text
Green
```

## Verifying

```text
Cyan
```

## Verified

```text
Green
```

## Failed

```text
Red
```

## Cancelled

```text
Gray
```

---

# 10. Status Representation

Do not communicate status using color alone.

Use:

```text
Color
+
Icon
+
Label
```

Example:

```text
● IN PROGRESS
```

or:

```text
[✓] Verified
```

or:

```text
[!] Approval Required
```

This improves accessibility and clarity.

---

# 11. Department Colors

Departments can have subtle identity colors.

Recommended:

```text
CEO / Executive
Indigo

CTO / Engineering
Blue

CMO / Marketing
Purple

Sales
Green

Finance
Emerald / Teal

Operations
Slate
```

These colors should be used subtly.

Examples:

* Agent avatar
* Small department indicator
* Chart series
* Org chart node accent
* Task metadata

Do not make entire screens bright department colors.

---

# 12. Typography

Typography should communicate:

```text
Authority
+
Clarity
+
Technical Precision
```

Recommended primary font:

# Inter

Inter should be the default application font.

Use it for:

* Navigation
* Dashboard
* Buttons
* Tables
* Forms
* Cards
* Agent information
* Tasks
* Metrics

Example:

```css
font-family:
  Inter,
  ui-sans-serif,
  system-ui,
  sans-serif;
```

---

# 13. Display Typography

Large headings can use the same font family.

Recommended:

```text
Font:
Inter

Weight:
600–700

Letter spacing:
-0.02em to -0.03em
```

Example:

```text
Company Overview
```

Should feel strong but not oversized.

---

# 14. Heading Scale

Recommended:

```text
Display:
36px / 44px
Weight 700

H1:
30px / 38px
Weight 700

H2:
24px / 32px
Weight 650

H3:
20px / 28px
Weight 600

H4:
16px / 24px
Weight 600
```

Avoid using extremely large headings inside operational dashboards.

---

# 15. Body Typography

Recommended:

```text
Large:
16px / 24px

Normal:
14px / 22px

Small:
13px / 20px

Caption:
12px / 18px
```

The default dashboard body size should generally be:

```text
14px
```

This allows information-dense enterprise interfaces without becoming difficult to read.

---

# 16. Font Weight

Use a limited number of weights.

```text
400 — Regular
500 — Medium
600 — Semibold
700 — Bold
```

Avoid excessive use of 800/900.

Recommended usage:

```text
400 → body

500 → navigation / metadata

600 → headings / buttons

700 → important metrics
```

---

# 17. Monospace Font

Use a monospace font for technical information.

Recommended:

```text
JetBrains Mono
```

Use it for:

* Task IDs
* Agent IDs
* Run IDs
* API values
* Logs
* Code
* JSON
* Tool calls
* System events
* Technical metadata

Example:

```text
TASK-8F42A
RUN-19283
agent.cto.backend
```

Do not use monospace for normal prose.

---

# 18. Typography Rules

Never use typography as decoration.

Do:

```text
Company Overview
127 Active Tasks
```

Avoid:

```text
C O M P A N Y   O V E R V I E W
```

Avoid excessive uppercase text.

Uppercase should mainly be used for:

* Small labels
* Status indicators
* Navigation categories
* Technical metadata

---

# 19. Spacing System

Use a consistent spacing scale.

Recommended base unit:

```text
4px
```

Scale:

```text
4
8
12
16
20
24
32
40
48
64
80
96
```

Common usage:

```text
4px  → icon/text gap

8px  → compact element spacing

12px → form elements

16px → card internal spacing

24px → card padding / section spacing

32px → major sections

48px → page sections

64px → large page separation
```

---

# 20. Layout

Desktop application layout:

```text
┌─────────────────────────────────────────────────────────┐
│ Top Bar                                                  │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│              │                                          │
│   Sidebar    │             Main Content                 │
│              │                                          │
│              │                                          │
│              │                                          │
└──────────────┴──────────────────────────────────────────┘
```

Recommended desktop dimensions:

```text
Sidebar:
240–280px

Top bar:
56–64px

Main content:
Flexible

Maximum content width:
1600px+
```

The application should support large monitors because company dashboards can contain substantial operational data.

---

# 21. Sidebar

The sidebar is the primary navigation.

Recommended structure:

```text
┌─────────────────────┐
│ AI COMPANY          │
│ OS                  │
├─────────────────────┤
│                     │
│ ◉ Overview           │
│                     │
│ COMPANY             │
│   Company            │
│   Departments        │
│   Agents             │
│                     │
│ WORK                 │
│   Projects           │
│   Tasks              │
│   Approvals          │
│                     │
│ KNOWLEDGE            │
│   Documents          │
│   Memory             │
│                     │
│ SYSTEM               │
│   Activity           │
│   Automations        │
│   Settings           │
│                     │
├─────────────────────┤
│ CEO Status           │
│ ● Operational        │
└─────────────────────┘
```

Keep navigation compact.

---

# 22. Top Bar

The top bar should contain:

```text
Page title
Breadcrumbs
Search
Notifications
Approval indicator
Voice control
User profile
```

Example:

```text
Company / Projects / AI Launch

                         🔎   🔔  3   🎙️   User
```

---

# 23. CEO Interface

The CEO should have a dedicated command interface.

It should not look like a normal ChatGPT clone.

Recommended structure:

```text
┌─────────────────────────────────────────────┐
│ CEO                                         │
│ Chief Executive Officer                     │
│ ● Operational                               │
├─────────────────────────────────────────────┤
│                                             │
│        What would you like to accomplish?   │
│                                             │
│  "Research the German AI market..."         │
│                                             │
│                         🎙️                  │
│                                             │
├─────────────────────────────────────────────┤
│ Current execution                           │
│                                             │
│ CMO       Market research        ● Running  │
│ Sales     Customer analysis      ● Running  │
│ CTO       Technical review       ✓ Done     │
│                                             │
└─────────────────────────────────────────────┘
```

The user should always be able to see:

```text
Command
→ Plan
→ Delegation
→ Execution
→ Results
```

---

# 24. Voice UI

Voice is a major interaction mode.

The microphone button should be prominent but not overwhelming.

States:

```text
Idle
Listening
Processing
Speaking
Error
```

Example:

```text
Idle:
○

Listening:
◉

Processing:
…

Speaking:
〰
```

Use subtle animation.

Do not create large pulsing neon circles.

---

# 25. CEO Conversation Design

Conversation should prioritize outcomes.

Instead of:

```text
CEO:
Hello! How can I help you today?
```

Prefer:

```text
CEO

Ready.

Current company status:
12 active projects
43 active tasks
3 approvals waiting

What would you like to accomplish?
```

The CEO should behave like an executive assistant, not a customer-support chatbot.

---

# 26. Dashboard Design

The dashboard is the company's control center.

Recommended structure:

```text
┌─────────────────────────────────────────────────────┐
│ Good evening                                        │
│ Company Overview                                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Revenue       Projects       Tasks       Agents     │
│ €124K         12             43          9          │
│                                                     │
├──────────────────────┬──────────────────────────────┤
│ Active Work          │ Approvals                    │
│                      │                              │
│ Project A            │ Contract review              │
│ Project B            │ Campaign publish             │
│ Project C            │ Budget request               │
│                      │                              │
├──────────────────────┴──────────────────────────────┤
│ Company Activity                                     │
│                                                     │
│ CTO → GitHub → Pull Request                         │
│ CMO → Research → Completed                          │
│ Sales → Lead analysis → Running                     │
└─────────────────────────────────────────────────────┘
```

---

# 27. Metric Cards

Metric cards should be simple.

Example:

```text
ACTIVE PROJECTS

12

↑ 3 this month
```

Avoid:

* Huge icons
* Large gradients
* Excessive decoration
* Multiple competing numbers

The number should be the primary visual element.

---

# 28. Agent Cards

Agent cards should show:

```text
Avatar
Name
Role
Department
Status
Current task
Last activity
```

Example:

```text
┌──────────────────────────────────┐
│ ●  CTO                            │
│    Chief Technology Officer       │
│                                  │
│    ● Working                      │
│                                  │
│    Reviewing authentication PR    │
│                                  │
│    Last active 2m ago             │
└──────────────────────────────────┘
```

---

# 29. Agent Detail Page

Structure:

```text
Agent Header
    ↓
Identity
    ↓
Responsibilities
    ↓
Current Tasks
    ↓
Recent Activity
    ↓
Tools
    ↓
Permissions
    ↓
Performance
    ↓
Memory
```

Example:

```text
CTO
Chief Technology Officer

● Operational

Responsibilities
Engineering strategy
Architecture
Technical execution

Current Work
...

Tools
GitHub
Documents
Code execution

Permissions
Read: Engineering
Write: Tasks
Restricted: Production deployment
```

---

# 30. Organization Chart

The organization page should visualize the hierarchy.

```text
                         CEO
                          │
          ┌───────────────┼───────────────┐
          │               │               │
         CTO             CMO            SALES
          │               │               │
     ┌────┼────┐       ┌──┴──┐        ┌──┴──┐
     │    │    │       │     │        │     │
 Architect AI   QA    Strategy Copy   Research Analyst
```

Use a clean node-based visual system.

Do not overuse shadows or gradients.

---

# 31. Task Interface

Task pages should emphasize execution state.

Example:

```text
Research German AI Market

TASK-8F42A

Status:
● IN PROGRESS

Assigned:
CMO → Marketing Strategist

Priority:
High

Created:
CEO

Dependencies:
✓ Customer research
○ Market research
○ Financial analysis

Current step:
Analyzing competitors

Tools:
Web Search
Documents

Activity:
...
```

---

# 32. Task Status Timeline

Use a timeline for important tasks.

```text
✓ Created
│
✓ Planned
│
✓ Assigned
│
✓ In Progress
│
● Verification
│
○ Completed
```

This helps users understand execution history.

---

# 33. Approval UI

Approvals should be visually distinct.

Example:

```text
┌───────────────────────────────────────────┐
│ APPROVAL REQUIRED                         │
│                                           │
│ Publish marketing campaign                │
│                                           │
│ Requested by: CMO                         │
│ Campaign: Germany AI Launch               │
│                                           │
│ Action: External publication              │
│                                           │
│ [ Review ]        [ Approve ] [ Reject ] │
└───────────────────────────────────────────┘
```

The system should explain:

```text
What will happen?
Who requested it?
Why is approval required?
What information will be sent?
What permissions are involved?
```

---

# 34. Activity Feed

Activity should read like an operational log.

Example:

```text
09:42  CMO
       Completed market research
       ✓ Verified

09:40  CTO
       Created GitHub pull request
       PR #183

09:38  Sales
       Completed enterprise customer analysis

09:35  CEO
       Created launch project
```

Use timestamps and agent identity consistently.

---

# 35. Real-Time Activity

When agents are working, users should see live status.

Example:

```text
CEO
● Coordinating

├── CMO
│   ● Researching market
│
├── Sales
│   ● Analyzing customers
│
└── CTO
    ✓ Technical analysis complete
```

Animations should be subtle.

---

# 36. Cards

Cards should be used to group meaningful information.

Recommended:

```text
border-radius:
10px–14px
```

Avoid making every UI element a card.

Too many cards create visual fragmentation.

---

# 37. Borders

Prefer borders over heavy shadows.

Dark theme:

```text
1px solid #27272A
```

Light theme:

```text
1px solid #E4E4E7
```

Shadows should primarily indicate elevation or overlays.

---

# 38. Border Radius

Recommended:

```text
Buttons:
8px

Inputs:
8px

Cards:
12px

Panels:
12–16px

Modal:
16px

Large containers:
16px
```

Avoid excessive pill-shaped components.

Pills should primarily represent:

* Status
* Tags
* Filters
* Categories

---

# 39. Buttons

Primary button:

```text
[ Create Project ]
```

Secondary:

```text
[ View Details ]
```

Danger:

```text
[ Reject ]
```

Ghost:

```text
[ Cancel ]
```

Button hierarchy should be clear.

Avoid multiple primary buttons competing within one section.

---

# 40. Icons

Use a consistent icon library.

Recommended:

```text
Lucide
```

Icons should generally be:

```text
16px
18px
20px
24px
```

Use icons to reinforce meaning.

Do not use icons as decoration everywhere.

---

# 41. Tables

Tables are important for:

* Tasks
* Agents
* Projects
* Customers
* Approvals
* Activity
* Tool executions

Example:

```text
Task              Agent        Status       Updated

Market Research  CMO          Running      2m ago
Customer Analysis Sales        Completed    8m ago
Architecture     CTO          Reviewing    12m ago
```

Tables should support:

* Sorting
* Filtering
* Search
* Pagination
* Row actions

---

# 42. Data Visualization

Charts should be simple and informative.

Recommended chart types:

```text
Line
Bar
Area
Donut
Progress
Timeline
```

Use charts for:

* Revenue
* Task completion
* Agent utilization
* Project progress
* Sales pipeline
* Cost
* AI usage
* Error rates

Avoid decorative charts.

---

# 43. Empty States

Empty states should be helpful.

Example:

```text
No active projects

Your company does not have any active projects yet.

[ Create Project ]
```

Avoid:

```text
Nothing here :(
```

---

# 44. Loading States

Use skeleton loading for page-level data.

Example:

```text
████████████
████████
████████████████
```

For AI operations use meaningful status:

```text
CEO is planning…
```

rather than only a generic spinner.

---

# 45. Error States

Errors should explain:

```text
What happened
Why it happened if known
What the user can do
```

Example:

```text
Unable to load agent status.

The agent service did not respond within the expected time.

[ Retry ]
```

Never expose raw stack traces to normal users.

---

# 46. AI Thinking / Processing UI

Do not display hidden chain-of-thought.

Instead display high-level execution status.

Good:

```text
CEO is planning the task…
```

```text
CEO delegated work to CMO and Sales.
```

```text
CMO completed market research.
```

Avoid exposing internal reasoning such as:

```text
I think X because Y...
```

The interface should show **actions, status, evidence, and results**, not private reasoning.

---

# 47. AI Response Structure

CEO responses should be structured.

Example:

```text
## Germany Launch Research

### Summary

The research is complete.

### Findings

• Market research completed
• Customer research completed
• Technical analysis completed

### Recommendation

The available evidence supports proceeding to the next planning stage.

### Next Step

A launch plan can now be prepared.

[ Create Launch Plan ]
```

---

# 48. Evidence UI

Important AI claims should have supporting evidence.

Example:

```text
Market size estimate

€2.4B

Sources:
3 verified sources

[ View Evidence ]
```

For task completion:

```text
✓ Verified

Evidence:
GitHub PR #183
Tests: 42 passed
```

---

# 49. Tool Execution UI

Tool calls should be visible at the appropriate level.

Example:

```text
CMO
Running Web Search

Tool:
web_search

Status:
● Running

Queries:
3

Results:
18
```

After completion:

```text
✓ Web Search completed

18 sources analyzed
```

Do not expose sensitive tool arguments or credentials.

---

# 50. Permission UI

Every agent should have visible permission boundaries.

Example:

```text
CTO Permissions

READ
✓ Engineering documents
✓ Project data

WRITE
✓ Tasks
✓ GitHub branches

RESTRICTED
🔒 Production deployment
🔒 Secret management
🔒 Infrastructure deletion
```

This reinforces trust.

---

# 51. Responsive Design

Desktop is the primary environment.

Support:

```text
Desktop
Tablet
Mobile
```

Recommended breakpoints:

```text
sm: 640px
md: 768px
lg: 1024px
xl: 1280px
2xl: 1536px
```

---

# 52. Mobile Design

Mobile should focus on:

```text
CEO
Tasks
Approvals
Notifications
Activity
Voice
```

Mobile navigation can use:

```text
Bottom navigation
```

Example:

```text
┌─────────────────────────────┐
│ Company                     │
│                             │
│       Dashboard             │
│                             │
│                             │
├─────────────────────────────┤
│ CEO     Tasks    Approvals  │
└─────────────────────────────┘
```

Voice should be especially accessible on mobile.

---

# 53. Accessibility

The product must follow accessible design principles.

Requirements:

* Keyboard navigation
* Visible focus states
* Sufficient color contrast
* Screen-reader labels
* Semantic HTML
* Accessible form controls
* Accessible dialogs
* No color-only status indicators
* Reduced-motion support

Support:

```text
prefers-reduced-motion
```

Animations should be optional.

---

# 54. Animation

Animation should communicate state.

Use:

```text
150–200ms
```

for common UI transitions.

Examples:

* Sidebar transitions
* Dropdowns
* Modal opening
* Status changes
* Task updates

Long animations should be avoided.

AI activity may use slightly longer subtle transitions.

---

# 55. Motion Principles

Use animation for:

```text
Change
Progress
Feedback
Hierarchy
```

Do not animate:

```text
Everything
```

The interface should remain calm even when many agents are working.

---

# 56. Notifications

Notifications should be categorized.

```text
INFO
SUCCESS
WARNING
ERROR
APPROVAL
```

Approval notifications should receive stronger visual priority than ordinary activity.

---

# 57. Search

Global search should be accessible from the top bar.

Search across:

```text
Agents
Tasks
Projects
Documents
Customers
Activity
Company knowledge
```

Example:

```text
Search company…

⌘ K
```

A command palette should eventually be supported.

---

# 58. Command Palette

Recommended shortcut:

```text
Cmd/Ctrl + K
```

Example:

```text
┌─────────────────────────────────────────┐
│ Search or run a command...              │
├─────────────────────────────────────────┤
│ Ask CEO                                  │
│ Create project                           │
│ Find task                                │
│ View approvals                           │
│ Open agents                              │
│ Search documents                         │
└─────────────────────────────────────────┘
```

---

# 59. Voice + Command Palette

Both interfaces should connect to the same command system.

```text
Voice
   │
   ├──────────────┐
   │              │
   ▼              ▼
Voice Intent   Command Intent
   │              │
   └──────┬───────┘
          ▼
       CEO
```

There should not be separate business logic for voice commands.

---

# 60. Design Tokens

Centralize all design values.

Recommended token categories:

```text
colors
typography
spacing
radius
shadows
borders
z-index
motion
breakpoints
```

Example:

```text
design/
├── tokens/
│   ├── colors.css
│   ├── typography.css
│   ├── spacing.css
│   ├── shadows.css
│   ├── radius.css
│   └── motion.css
```

---

# 61. Component Design

Reusable components should include:

```text
Button
Input
Select
Checkbox
Badge
StatusBadge
Card
MetricCard
AgentCard
TaskCard
ProjectCard
DataTable
Modal
Drawer
Tabs
Dropdown
Tooltip
Toast
CommandPalette
ApprovalPanel
ActivityFeed
Timeline
Chart
VoiceButton
CEOCommandBox
```

---

# 62. Component Architecture

Components should be divided into:

```text
Primitive
    ↓
UI Component
    ↓
Domain Component
    ↓
Page
```

Example:

```text
Badge
  ↓
StatusBadge
  ↓
TaskStatus
  ↓
TaskDetailsPage
```

Avoid putting business logic directly into primitive UI components.

---

# 63. Frontend Folder Design

Recommended:

```text
apps/web/

├── app/
│
├── components/
│   ├── ui/
│   ├── layout/
│   ├── dashboard/
│   ├── agents/
│   ├── tasks/
│   ├── projects/
│   ├── approvals/
│   ├── activity/
│   └── voice/
│
├── features/
│   ├── company/
│   ├── agents/
│   ├── tasks/
│   ├── projects/
│   ├── approvals/
│   ├── voice/
│   └── ceo/
│
├── lib/
│   ├── api/
│   ├── auth/
│   └── utils/
│
├── hooks/
│
├── stores/
│
└── styles/
    └── globals.css
```

---

# 64. Design Relationship With Architecture

The frontend should reflect the backend architecture.

```text
USER
 │
 ▼
UI
 │
 ▼
API
 │
 ▼
CEO
 │
 ▼
TASK ENGINE
 │
 ▼
AGENTS
 │
 ▼
TOOLS
```

The interface should visually expose this flow where useful.

---

# 65. Company State Visualization

The company has a central operational state.

The dashboard should make it possible to understand:

```text
Company
│
├── Strategy
├── Projects
├── Departments
├── Agents
├── Tasks
├── Customers
├── Documents
├── Approvals
└── Activity
```

This should feel like a connected system rather than isolated pages.

---

# 66. CEO as the Primary Interaction

The product should support two complementary modes:

### Command Mode

```text
"CEO, research the German market."
```

### Control Mode

User manually explores:

```text
Dashboard
→ Project
→ Tasks
→ Agent
→ Evidence
→ Approval
```

Voice and UI should always operate on the same underlying company state.

---

# 67. Trust Design

Trust should come from transparency.

The interface should show:

```text
Who
What
When
Why
Status
Evidence
Permission
Approval
```

For example:

```text
WHO
CMO

WHAT
Created campaign draft

WHEN
2 minutes ago

STATUS
Waiting for approval

EVIDENCE
Campaign document

PERMISSION
Draft allowed
Publishing restricted
```

---

# 68. Executive Density

The CEO dashboard should have high information density without feeling crowded.

Recommended approach:

```text
Large whitespace between sections
+
Compact information inside sections
```

Use visual hierarchy rather than excessive spacing everywhere.

---

# 69. Dark Theme Priority

Dark theme is recommended as the primary product identity because:

* AI operations often involve technical information
* Long sessions benefit from controlled luminance
* Activity/log interfaces work well in dark mode
* It gives the product a professional operations-center feel

However, light mode must remain fully supported.

---

# 70. Brand Personality

The brand should communicate:

```text
Calm
Intelligent
Precise
Capable
Trustworthy
Technical
Executive
```

Avoid branding that communicates:

```text
Chaotic
Cute
Toy-like
Overly futuristic
Aggressive
Gamer-oriented
```

---

# 71. Recommended Visual Identity

Primary identity:

```text
Indigo
+
Near-black
+
White
+
Slate
```

Secondary accents:

```text
Violet
Cyan
Green
Amber
Red
```

The primary UI should remain mostly neutral.

Accent colors should communicate state or hierarchy.

---

# 72. Logo Direction

The logo should represent:

```text
Company
+
Intelligence
+
Coordination
```

Possible visual concepts:

```text
Network nodes
Organizational hierarchy
Abstract C
Neural network
Connected system
Command center
```

Avoid generic robot-head logos.

---

# 73. Iconography

Use consistent stroke-based icons.

Recommended characteristics:

```text
2px stroke
Rounded joins
Minimal detail
Consistent size
```

Lucide-style iconography is recommended.

---

# 74. Voice Indicator

The CEO voice indicator can become a recognizable product element.

Concept:

```text
○
```

Idle

```text
◉
```

Listening

```text
≈≈≈
```

Processing / voice activity

The animation should remain subtle and accessible.

---

# 75. Agent Presence

Agents can have lightweight presence indicators:

```text
● Online

● Working

○ Idle

◐ Waiting

!
Attention Required

× Offline
```

Presence must reflect actual system state.

Never show an agent as "Working" when there is no active execution.

---

# 76. AI Activity Language

Use operational language.

Prefer:

```text
Planning
Delegating
Executing
Waiting
Verifying
Completed
Blocked
Failed
```

Avoid:

```text
Thinking deeply...
Feeling confident...
Being creative...
Working my magic...
```

The product is an operational system.

---

# 77. CEO Response Tone

The visual design should support a CEO communication style that is:

```text
Concise
Direct
Structured
Evidence-based
Action-oriented
```

The UI should make concise responses easy to scan.

---

# 78. Information Hierarchy Example

For a project page:

```text
PROJECT NAME
↓
PROJECT STATUS
↓
OBJECTIVE
↓
PROGRESS
↓
ACTIVE TASKS
↓
AGENTS
↓
BLOCKERS
↓
APPROVALS
↓
ARTIFACTS
↓
ACTIVITY
```

This order should remain consistent.

---

# 79. Mobile Information Hierarchy

On mobile:

```text
Status
↓
Primary objective
↓
Critical tasks
↓
Approvals
↓
CEO command
↓
Activity
```

Secondary information can be hidden behind expandable sections.

---

# 80. Design System Rules

### Rule 1

Use semantic colors.

### Rule 2

Do not use color only to communicate meaning.

### Rule 3

Use one primary action per major section.

### Rule 4

Do not turn every element into a card.

### Rule 5

Prefer borders over heavy shadows.

### Rule 6

Keep typography consistent.

### Rule 7

Use animation to communicate state.

### Rule 8

Never expose secrets.

### Rule 9

Do not expose private chain-of-thought.

### Rule 10

Show evidence for important AI-generated claims.

### Rule 11

Make approvals visually obvious.

### Rule 12

Show real system state, not simulated AI state.

### Rule 13

Keep the CEO interface central.

### Rule 14

Keep the dashboard operational rather than decorative.

### Rule 15

Use the same design language across every department.

---

# 81. Design System Technology

Recommended frontend design stack:

```text
Next.js
TypeScript
React
Tailwind CSS
Lucide Icons
CSS Variables
```

Optional:

```text
Radix UI
shadcn/ui
TanStack Table
Recharts
Framer Motion
```

The project should avoid becoming dependent on a large collection of unrelated UI libraries.

---

# 82. Recommended UI Foundation

A good foundation would be:

```text
Tailwind CSS
+
CSS Design Tokens
+
shadcn/ui-style primitives
+
Lucide Icons
+
Custom Company OS components
```

Generic components should be customized to match the product identity.

Do not ship a completely unmodified template.

---

# 83. Design Development Order

Build the visual system in this order:

```text
1. Color tokens
2. Typography
3. Spacing
4. Layout
5. Buttons
6. Inputs
7. Badges
8. Cards
9. Navigation
10. Tables
11. Modals
12. Agent components
13. Task components
14. Approval components
15. CEO interface
16. Dashboard
17. Voice interface
18. Charts
19. Real-time activity
20. Responsive/mobile
```

---

# 84. Phase-Based Design Implementation

## Phase 1 — Foundation

Implement:

* Colors
* Typography
* Spacing
* Buttons
* Inputs
* Icons
* Theme switching

---

## Phase 2 — Application Shell

Implement:

* Sidebar
* Top bar
* Responsive layout
* Navigation
* User menu
* Notifications

---

## Phase 3 — Dashboard

Implement:

* Metrics
* Active projects
* Tasks
* Approvals
* Activity
* Agent status

---

## Phase 4 — Company

Implement:

* Company profile
* Departments
* Organization chart
* Agent registry

---

## Phase 5 — CEO

Implement:

* CEO command center
* Conversation
* Voice
* Execution status
* Delegation visualization

---

## Phase 6 — Work Management

Implement:

* Projects
* Tasks
* Task timeline
* Dependencies
* Agent assignments

---

## Phase 7 — Approvals

Implement:

* Approval queue
* Approval details
* Review interface
* Approve/reject actions
* Audit information

---

## Phase 8 — Knowledge

Implement:

* Documents
* Search
* Company memory
* Evidence
* Source references

---

## Phase 9 — Real-Time Operations

Implement:

* Live activity
* Agent presence
* Task execution
* Tool execution
* Notifications

---

## Phase 10 — Voice

Implement:

* Microphone control
* Listening state
* Processing state
* Speaking state
* Voice conversation history

---

# 85. Final Design Direction

The final application should visually feel like:

```text
                 AI COMPANY OS

       ┌─────────────────────────────┐
       │ CEO                         │
       │ ● Operational               │
       │                             │
       │ "What should we accomplish?"│
       │                         🎙️  │
       └─────────────────────────────┘

 ┌──────────┬──────────┬──────────────┐
 │ Projects │ Tasks    │ Approvals    │
 │ 12       │ 43       │ 3            │
 └──────────┴──────────┴──────────────┘

 ┌─────────────────────────────────────┐
 │ Active Company Operations           │
 │                                     │
 │ CEO  → CMO     Market Research      │
 │      → Sales   Customer Analysis    │
 │      → CTO     Technical Review     │
 │                                     │
 └─────────────────────────────────────┘

 ┌─────────────────────────────────────┐
 │ Organization                        │
 │                                     │
 │              CEO                    │
 │        ┌──────┼──────┐              │
 │       CTO    CMO   SALES             │
 │                                     │
 └─────────────────────────────────────┘
```

The visual identity should communicate:

> **"This is the control center for an AI-powered company."**

Not:

> "This is another AI chat application."

---

# 86. Final Design Checklist

Before considering the design system complete:

### Theme

* [ ] Dark theme
* [ ] Light theme
* [ ] Semantic color tokens
* [ ] Accessible contrast
* [ ] Status colors
* [ ] Department colors

### Typography

* [ ] Inter
* [ ] JetBrains Mono
* [ ] Heading scale
* [ ] Body scale
* [ ] Font weights
* [ ] Line heights

### Layout

* [ ] Sidebar
* [ ] Top bar
* [ ] Main content
* [ ] Responsive layout
* [ ] Mobile navigation

### Components

* [ ] Buttons
* [ ] Inputs
* [ ] Cards
* [ ] Badges
* [ ] Tables
* [ ] Modals
* [ ] Drawers
* [ ] Toasts
* [ ] Tabs
* [ ] Tooltips

### AI Components

* [ ] CEO command center
* [ ] Voice button
* [ ] Agent cards
* [ ] Agent status
* [ ] Task timeline
* [ ] Delegation visualization
* [ ] Tool execution
* [ ] Evidence
* [ ] Approval interface

### Operations

* [ ] Real-time activity
* [ ] Notifications
* [ ] Loading states
* [ ] Error states
* [ ] Empty states
* [ ] Verification states

### Accessibility

* [ ] Keyboard navigation
* [ ] Focus states
* [ ] Screen-reader support
* [ ] Color contrast
* [ ] Reduced motion
* [ ] No color-only communication

---

# 87. Design Golden Rules

1. **The UI is a company control center, not a chatbot.**
2. **The CEO is the primary interaction point.**
3. **Company state must be visible.**
4. **Agent activity must be transparent.**
5. **Important actions must show their status.**
6. **Approvals must be impossible to miss.**
7. **Evidence should accompany important results.**
8. **Colors communicate meaning.**
9. **Typography communicates hierarchy.**
10. **Animation communicates state.**
11. **Dark mode is the primary visual identity.**
12. **Light mode remains fully supported.**
13. **Use neutral surfaces and restrained accents.**
14. **Avoid visual noise.**
15. **Never expose secrets or private AI reasoning.**
16. **The interface must represent real system state.**
17. **Human control must remain obvious.**
18. **Voice and UI must operate on the same company state.**
19. **Consistency is more important than visual novelty.**
20. **The design should make a complex AI organization feel simple to operate.**

---

# 88. One-Sentence Design Definition

> **AI Company OS is a dark-first, executive-grade AI operations interface that combines the clarity of an enterprise dashboard, the precision of a developer platform, and the natural interaction of a voice-controlled CEO.**
