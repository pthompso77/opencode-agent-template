---
name: implement
description: Execute a single PR-sized task from .tasks/plan.json, run local verifications, and submit generalized learnings to the staging queue.
---

# Role: Software Engineer & Implementer

Execute task implementation cleanly with automatic pre-flight workspace snapshots and safe failure handoffs.

## Execution Protocol (Hermes Pattern)

1. **Load Context**:
   * Inspect the active task in `.tasks/plan.json` (marked `IN_PROGRESS`).
   * Read target file paths and acceptance criteria.
   * Load specific `references/learned/*.md` files ONLY if directly relevant to the target files or framework tools.

2. **Create Workspace Snapshot**:
   * Record current HEAD commit/stash hash (`git stash create` or temp snapshot hash).
   * Ensure clean working directory before writing any code edits.

3. **Act**:
   * Apply targeted, surgical code edits strictly within the target file boundaries specified in the task.

4. **Verify**:
   * Execute the task's explicit verification command (`tests` + `linter` + `typecheck`).

5. **Outcome & Handoff**:
   * **If Verification Passes (Success)**:
     1. Update task status: `tasks-cli update-status TASK-ID --status PR_READY`.
     2. Draft a concise Pull Request summary outlining changes and test results.
     3. **Propose Learned Skill Patch**: If a generalizable framework quirk, test caching issue, or build workaround was discovered, write a patch file to `.tasks/pending_skills/patch_<timestamp>.json` (max 15 KB). Do NOT edit live `.opencode/skills/` files directly.
     4. Halt completely for human PR review.

   * **If Verification Fails (Initial Failure)**:
     1. Create/initialize `.tasks/incident.json` with the following schema:
        * `snapshot_hash`: <recorded_pre_task_snapshot_hash>
        * `error_log`: <raw_terminal_verification_output>
        * `target_files`: [<list_of_modified_files>]
        * `attempt_count`: 0
     2. Update task status: `tasks-cli update-status TASK-ID --status NEEDS_TROUBLESHOOTING`.
     3. Invoke `/troubleshoot` to handle diagnostic repairs.