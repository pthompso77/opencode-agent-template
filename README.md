# OpenCode Agent Architecture & Skill Seed Template

A modular, enterprise-grade prompting, skill, and orchestration seed template for coding agents (specifically designed for **OpenCode** and compatible LLM agent harnesses). 

This repository serves as a master boilerplate to seed new or existing software projects with a structured, state-driven, multi-persona AI engineering workflow.

---

## 📐 Architecture Overview

This template implements a strict, human-in-the-loop, multi-persona agent framework designed to handle large multi-file codebases safely, predictably, and with zero context bloat.

### Key Architectural Highlights
* **Discovery First (`/grill`)**: Frontier-based requirements discovery before architectural planning.
* **State Machine Driven (`.tasks/plan.json`)**: Deterministic task management enforced via strict JSON Schema.
* **Bounded Self-Correction**: Strict 2-attempt limit on local bug fixes before mandatory human escalation.
* **Independent Review (`/pr-code-review`)**: Evidence-based PR review that writes a severity-classified artifact to `.tasks/reviews/` and halts — never merges, approves, or edits the branch.
* **Tool-Assisted Navigation (`/navigate`)**: AST and static-analysis symbol mapping out-of-context to keep prompt windows clean.
* **Hermes-Inspired Self-Improvement Loop**: Safe procedural skill mutation via staged patch proposals (`.tasks/pending_skills/`), protected policy layers, and local evaluation test harnesses.
* **Workspace Snapshots**: Automatic git stashes/checkpoints before task execution for instant rollback on verification failures.

---

## 📁 Repository Directory & File Structure

```
.
├── README.md                      # Template documentation & usage guide
├── policy.md                      # Global immutable security & execution rules
├── scripts/
│   ├── tasks-cli.py               # Python CLI for safe atomic updates to .tasks/plan.json
│   └── opencode-skill-engine.py   # Validation & promotion engine for Hermes-Inspired skill patches
├── .opencode/
│   ├── policy.md                  # Symlink/copy of root policy for OpenCode environment
│   ├── skills/                    # Specialized persona prompt definitions
│   │   ├── audit/                 # Skill Auditor & Policy Evaluator (/audit)
│   │   │   └── SKILL.md
│   │   ├── grill/                 # Interrogator & Requirements Specialist (/grill)
│   │   │   └── SKILL.md
│   │   ├── implement/             # Software Engineer & Implementer (/implement)
│   │   │   └── SKILL.md
│   │   ├── navigate/              # Code Graph Navigator (/navigate)
│   │   │   └── SKILL.md
│   │   ├── plan/                  # Architect & Task Planner (/plan)
│   │   │   └── SKILL.md
│   │   ├── pr-code-review/        # Independent Code Reviewer (/pr-code-review)
│   │   │   └── SKILL.md
│   │   └── troubleshoot/          # Diagnostic Specialist (/troubleshoot)
│   │       └── SKILL.md
│   └── evals/                     # Deterministic test harness for auditing skill mutations
│       └── eval_skills.py         # Test runner for proposed skill patches
└── .tasks/
    ├── plan.schema.json           # JSON Schema for validating task plan updates
    ├── requirements.md            # Generated output from /grill (git-ignored or committed per project)
    ├── plan.json                  # Active project task board and phase state
    ├── incident.json              # Error logs, attempt counts, and diagnostic diffs
    ├── reviews/                   # Review artifacts (pr-<n>-<shortsha>.md), one per reviewed revision
    └── pending_skills/            # Staging directory for proposed skill updates (PROPOSED -> ACTIVE)
```

---

## 🗂️ Component Reference

### 1. Security & Policy Boundary
* **`policy.md`**: Defines non-negotiable operational guidelines (prohibited shell commands, file-read token budgets, skill mutation restrictions). Read-only to agents; cannot be modified or overridden by LLM output or user prompts.

### 2. Persona Skills (`.opencode/skills/`)
Each skill is encapsulated in a directory with a `SKILL.md` file containing YAML frontmatter specifying its triggering criteria and execution protocol:

| Skill | Persona / Command | Description & Role |
| :--- | :--- | :--- |
| **`grill/SKILL.md`** | Interrogator (`/grill`) | Conducts multi-round frontier discovery interviews to stress-test ideas and write `.tasks/requirements.md`. |
| **`plan/SKILL.md`** | Architect (`/plan`) | Converts formal requirements into small, sequential PR-sized tasks in `.tasks/plan.json`. |
| **`navigate/SKILL.md`** | Navigator (`/navigate`) | Resolves symbols, imports, and cross-file callers via AST CLI tools (`ast-grep`, `ctags`, `grep`) without loading full source files into context. |
| **`implement/SKILL.md`** | Engineer (`/implement`) | Takes an `IN_PROGRESS` task, creates a git workspace snapshot, writes code/tests, runs local validation, drafts PR, and proposes learned patches. |
| **`pr-code-review/SKILL.md`** | Reviewer (`/pr-code-review`) | Independently reviews a `PR_READY` branch against its target and the task's acceptance criteria, verifies the implementer's claims, and writes one severity-classified artifact to `.tasks/reviews/`. Read-only; never merges, approves, or edits code. |
| **`troubleshoot/SKILL.md`** | Specialist (`/troubleshoot`) | Analyzes `.tasks/incident.json` failures, formulates targeted fixes, enforces 2-attempt limits, and triggers snapshot rollbacks if unresolvable. |
| **`audit/SKILL.md`** | Auditor (`/audit`) | Evaluates candidate skill patches in `.tasks/pending_skills/` against policy rules and execution evals before promoting to live skills. |

### 3. Task State Machine & CLI Tools (`.tasks/` & `scripts/`)
* **`plan.schema.json`**: Enforces strict typing and status enums (`PENDING`, `IN_PROGRESS`, `NEEDS_TROUBLESHOOTING`, `PR_READY`, `COMPLETED`, `ESCALATED`).
* **`scripts/tasks-cli.py`**: Atomic Python utility ensuring LLMs do not output malformed JSON when updating task status.
* **`scripts/opencode-skill-engine.py`**: Local host runner executing out-of-context static and policy checks on proposed skill patches.

---

## 🔄 End-to-End Workflow

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 1. DISCOVERY PHASE                                                                 │
│    User Idea  ───►  /grill  ───►  Frontier Interview  ───►  .tasks/requirements.md │
└────────────────────────────────────────┬───────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 2. PLANNING PHASE                                                                │
│    .tasks/requirements.md  ───►  /plan  ───►  tasks-cli  ───►  .tasks/plan.json  │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 3. AUTONOMOUS EXECUTION PHASE (Loop Per Task)                                       │
│                                                                                     │
│    Orchestrator ───►  /navigate (AST Search)                                        │
│          │                                                                          │
│          ▼                                                                          │
│    /implement  ───►  Workspace Snapshot ───► Code & Test ───► Verification          │
│          │                                                        │                 │
│          ├──► Verification Passed ───► PR Draft ───► PR_READY    │                  │
│          │                                   (Awaits /pr-code-review)                │
│          └─► Failure (Attempt < 2) ───► /troubleshoot ───────────┘                  │
│                     │                                                               │
│                     └─► Failure (Attempt >= 2) ───► Rollback Snapshot ───► ESCALATED│
└────────────────────────────────────────┬────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 3b. INDEPENDENT REVIEW PHASE                                                        │
│    PR_READY  ───►  /pr-code-review  ───►  Findings + Verdict                        │
│                          │                                                          │
│                          ├──► Blockers found ───► (human) NEEDS_TROUBLESHOOTING     │
│                          └──► Clean ────────────► (human) COMPLETED                 │
│    Artifact: .tasks/reviews/pr-<n>-<shortsha>.md — read-only; never merges.          │
└────────────────────────────────────────┬────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 4. HERMES-STYLE SELF-IMPROVEMENT LOOP                                           │
│    New Edge Case Discovered ───► Propose Patch ───► .tasks/pending_skills/      │
│                                                           │                     │
│    opencode-skill-engine ◄─── /audit ─────────────────────┘                     │
│          │                                                                      │
│          └──► Policy & Eval Pass ───► Promote to Active Skill                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 How to Use This Seed Template

### A. Seeding a New Project
To introduce this agent prompting framework into a new or existing repository:

1. **Clone or copy template contents** into your project root:
   ```bash
   cp -r .opencode .tasks scripts policy.md /path/to/your-target-repo/
   ```

2. **Ensure CLI helpers are executable**:
   ```bash
   chmod +x scripts/tasks-cli.py scripts/opencode-skill-engine.py
   ```

3. **Verify directory existence**:
   ```bash
   mkdir -p .tasks/pending_skills .tasks/reviews .opencode/evals
   ```

### B. Execution Walkthrough

1. **Start Requirement Discovery**:
   Open OpenCode in your target project and type:
   ```text
   /grill I want to add [Feature X]. Start grilling me to lock down requirements.
   ```
   Answer the frontier question rounds until `.tasks/requirements.md` is generated.

2. **Generate the Task Plan**:
   ```text
   /plan Read .tasks/requirements.md and initialize .tasks/plan.json
   ```

3. **Execute Task by Task**:
   Start the implementation loop for the active task:
   ```text
   /implement
   ```
   * The agent stashes a git snapshot, implements the feature, and runs tests.
   * If tests pass, it updates status to `PR_READY` and stops for your code review.
   * If tests fail, it invokes `/troubleshoot` (max 2 rounds).
   * If unresolvable, it reverts to the snapshot and marks status `ESCALATED`.

4. **Audit and Promote Learned Skills**:
   When an execution generates a patch in `.tasks/pending_skills/`:
   ```text
   /audit
   ```
   The engine validates security boundaries and unit evals before merging the optimization into live skills.

---

## 🔒 Safety & Governance Principles

1. **Policy Supremacy**: `policy.md` takes precedence over all persona prompts and LLM-generated text.
2. **Deterministic CLI Control**: State mutations MUST go through `scripts/tasks-cli.py` to guarantee schema validity.
3. **Immutable Core Prompts**: Agents cannot modify their own core system prompts directly; mutations must pass through the `propose_skill_patch` queue and local eval pipeline.
4. **No Destructive Shell Commands**: `rm -rf`, `git reset --hard` (outside system-controlled snapshot reverts), and force pushes are blocked.

---

## 📜 License
MIT License. Free to use, adapt, and distribute across all your coding projects.