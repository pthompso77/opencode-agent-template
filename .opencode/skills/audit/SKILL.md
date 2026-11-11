---
name: audit
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
2. Execute local test harness: `opencode-skill-engine.py test <file>`.
3. If validation passes, promote the patch to `.opencode/skills/` (`opencode-skill-engine.py promote <file>`). If validation fails, discard the patch and log reasons.

## Propose Learned Skill Patch
If the audit process revealed any generalizable evaluation patterns, policy compliance strategies, or validation criteria that could improve future patch assessments, write a patch file to `.tasks/pending_skills/patch_<timestamp>.json` (max 15 KB). Do NOT edit live `.opencode/skills/` files directly.
## Patch Format Contract (enforced by eval_skills.py + opencode-skill-engine.py)

A pending patch's `content` field is a **complete replacement** for the target `SKILL.md`, not an append-proposal. The engine writes `content` verbatim over the destination file. A patch must satisfy all of the following, or the eval gate fails:

1. **`content` must start with a YAML frontmatter block** (`---` line, then `name:` and `description:` keys, then a closing `---`). `eval_skills.py` regex-matches `^---\n(.*?)\n---` and requires both keys. Append-proposals ("# Patch proposal: … (append to X)") fail this check with `Missing YAML frontmatter block`.
2. **`content` must be the full skill** — begin by copying the current live `SKILL.md`, then apply the intended change. Never write only the delta; the destination file is overwritten, not merged.
3. **`description` must stay ≤ 500 chars**; keep it as the existing invocation criteria unless the change intentionally narrows/widens the trigger.
4. **Budget interaction**: the patch `.json` file itself must stay ≤ 15 KB (checked by `check_file_limits`). Since the file wraps `content` with JSON escaping, the *content* byte size must be ~1–1.5 KB under the limit. If the target skill is already near 15 KB (e.g. `pr-code-review`), the additions cannot fit — condense the skill first (faithfully) so the combined file fits, or the patch will be rejected on size even after passing eval.
5. **`target_skill`** is the plain directory name of an existing skill (or a new one). No path separators, leading dots, or traversal.

### Heuristic
Before writing a patch, run `opencode-skill-engine.py test <file>` and expect it to fail on format unless the content is a full frontmatter-bearing SKILL.md. A patch that only describes an edit in prose has never been promotable in this harness; the self-improvement loop only completes when the proposal is a concrete replacement file.

