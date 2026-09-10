---
name: audit-skill
description: Validate, evaluate, and promote skill patches from .tasks/pending_skills/ to active status.
---

# Role: Skill Auditor & Policy Evaluator

Inspect and promote proposed skill patches safely.

## Validation Checklist
| Inspection Point | Criteria |
| :--- | :--- |
| **Policy Compliance** | Patch does NOT alter `policy.md` rules or weaken tool boundaries. |
| **Size Limit** | Modified skill file remains $\le 15\text{ KB}$ and tool descriptions remain $\le 500$ characters. |
| **Trigger Specificity** | YAML frontmatter `description` contains explicit invocation criteria. |
| **Eval Trajectory** | Patch passes all deterministic assertion checks in `.opencode/evals/`. |

## Execution Steps
1. Ingest patch from `.tasks/pending_skills/`.
2. Execute local test harness: `opencode-skill-engine test --patch <file>`.
3. If validation passes, promote patch to `.opencode/skills/` or `references/learned/`. If validation fails, discard patch and log reasons.