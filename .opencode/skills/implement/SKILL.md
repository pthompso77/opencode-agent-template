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

2. **Create Workspace Snapshot**:
    * Record current HEAD commit/stash hash (`git stash create` or temp snapshot hash).
    * Ensure clean working directory before writing any code edits.

3. **Create Feature Branch**:
    * Determine the task ID from `.tasks/plan.json` (e.g., `TASK-001`).
    * Check out a new branch: `git checkout -b feature/<task-id>` (e.g., `feature/TASK-001`).
    * All code edits and commits are made on this feature branch.
    * This allows human review via Pull Request before merging into the default branch (`dev` or `main`).

4. **Act**:
    * Apply targeted, surgical code edits strictly within the target file boundaries specified in the task.
    * Commit changes with a descriptive message referencing the task ID.

5. **Verify**:
    * Execute the task's explicit verification command (`tests` + `linter` + `typecheck`).

6. **Outcome & Handoff**:
    * **If Verification Passes (Success)**:
      1. Update task status: `tasks-cli.py update-status TASK-ID --status PR_READY`.
      2. Draft a concise Pull Request summary outlining changes and test results, referencing the `feature/<task-id>` branch for review before merging into the default branch.
      3. **Propose Learned Skill Patch**: If a generalizable framework quirk, test caching issue, or build workaround was discovered, write a patch file to `.tasks/pending_skills/patch_<timestamp>.json` (max 15 KB). Do NOT edit live `.opencode/skills/` files directly.
      4. Halt completely for human PR review.

    * **If Verification Fails (Initial Failure)**:
      1. Create/initialize `.tasks/incident.json` with the following schema:
         * `snapshot_hash`: <recorded_pre_task_snapshot_hash>
         * `error_log`: <raw_terminal_verification_output>
         * `target_files`: [<list_of_modified_files>]
         * `attempt_count`: 0
      2. Update task status: `tasks-cli.py update-status TASK-ID --status NEEDS_TROUBLESHOOTING`.
      3. Invoke `/troubleshoot` to handle diagnostic repairs.
## Step 3a: Pre-flight branch-collision check

Before `git checkout -b feature/<task-id>`, check whether that branch already exists locally or on the remote:

```bash
git branch --list "feature/<task-id>"
git ls-remote --heads origin "feature/<task-id>"
```

Task IDs are recycled whenever a plan is regenerated, so an existing branch may hold completely unrelated history. Because `policy.md` forbids force-pushes, never reset or reuse a colliding branch. Instead:

1. Derive a fresh, unambiguous branch name (e.g. `feature/<task-id>_v2` or a short slug of the task title) from the current base branch.
2. Confirm the base branch with the user when it is not obvious — the plan may live on a branch (e.g. `planning`) that is *not* the repo default (`main`/`dev`), and branching from the wrong base omits the very plan/requirements the task cites.
3. Record the base commit as the snapshot hash before any edits.

Ask the user before silently choosing a suffix when a collision is detected; it is a one-line question that prevents an unreviewable branch.

## Step 5a: Scaffold tasks must make their own verification command resolvable

A scaffold/foundation task's `verification_cmd` is often also the verification command for every later task (e.g. `uv run --directory <pkg> ruff check .`). If the tool runner (ruff/mypy/pytest) is not declared as a dependency, the command fails with `error: Failed to spawn: ruff`. When the scaffold task is the one that establishes the environment, add the shared dev toolchain to the project's dev dependency group even if it is not listed in `target_files` — this is the task that owns environment setup, and without it no downstream verification can run. Keep the edit inside the project's manifest (pyproject/package manifest) and note it in the PR summary.

### Heuristic
If a scaffold task owns the environment, its acceptance should include "the verification command for this task, and the toolchain it depends on, resolve inside the freshly synced environment." Verify by running the task's exact `verification_cmd` from the repo root, not from inside the package directory.

## Step 6b: Open the pull request with `gh`

When verification passes, do not merely draft a PR summary in chat — create the PR. The branch is already committed and (per the success path) pushed, so the run owns everything needed.

1. Push the feature branch if it is not already on the remote:

   ```bash
   git push -u origin feature/<task-id>
   ```

   Re-running is safe; an existing remote branch at the same commit is a no-op.

2. Confirm the PR base with the user if it is not obvious. It is frequently *not* the repo default: the plan and requirements often live on a working branch (e.g. `try2-initiate`, `planning`), and the correct base is whichever branch holds the plan this task came from. Do not guess silently when several candidates exist.

3. Create the PR against that base, passing the drafted summary as the body:

   ```bash
   gh pr create --base <base> --head feature/<task-id>      --title "<TASK-ID>: <title>" --body-file <summary-file>
   ```

   Write the body to a temp file (e.g. `/tmp/opencode/pr_body.md`) rather than inlining it, to avoid shell-quoting problems with the markdown.

4. Verify the result and capture the URL for the handoff:

   ```bash
   gh pr view <number> --json number,url,state,baseRefName,headRefName,mergeable
   ```

   Then halt for human review, reporting the PR URL.

### Pre-flight checks
- Run `gh auth status` once; if the CLI is unauthenticated, fall back to reporting the pushed branch and drafted summary rather than failing the run.
- Check `gh pr list --state all --head feature/<task-id>` first; if a PR already exists for the branch, update or report it instead of creating a duplicate.
- `gh pr create` on an up-to-date branch is idempotent enough for retries, but guard the call so a re-run does not open a second PR.

### Why this is part of 'implement', not a separate skill
Reviewability is the definition of done for a PR-sized task. A task is not 'ready for PR review' until the PR exists. The summary the skill already mandates is precisely the PR body; producing it and then not using it wastes the artifact and reintroduces a manual step the harness was built to remove.
