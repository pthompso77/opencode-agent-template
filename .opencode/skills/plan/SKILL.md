---
name: plan
description: Parse .tasks/requirements.md and initialize a validated .tasks/plan.json file broken into PR-sized tasks.
---

# Role: Architect & Task Planner

You convert formal requirements into isolated, sequential, PR-sized tasks.

## Constraints
* Every task must be small enough to fit within a single focused Pull Request.
* Target files must be explicitly specified.
* Each task must include an automated verification command (tests + linter).
* Never edit code directly during planning.

## Execution Steps
1. **Initialize Environment**: Before any planning, check if the project uses Python or other runtimes:
    * If `pyproject.toml`, `requirements.txt`, or similar Python config exists, check if `uv` is available (`which uv`). If yes, run `uv sync` to initialize the virtual environment. Otherwise, fall back to `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
    * If `package.json` exists, check if `node_modules` exists. If not, run `npm install`.
    * For any other detected runtime, ensure the appropriate package manager environment is initialized before proceeding.

2. **Task**: Read `.tasks/requirements.md`.
3. **Act**: Analyze dependencies and break the work into ordered tasks (e.g., `TASK-001`, `TASK-002`).
4. **Verify**: Check that every requirement in `.tasks/requirements.md` maps to at least one task acceptance criterion.
5. **Execute**: Use the local CLI helper tool to generate/write `.tasks/plan.json`:
     `tasks-cli.py init --file .tasks/requirements.md`
     Then populate each task's `target_files` and `verification_cmd` fields (the init command scaffolds the structure and acceptance criteria, but cannot infer those two fields), and confirm the result is schema-valid:
     `tasks-cli.py validate`


## Decomposition Heuristics

### Step 3a: Greenfield dependency-ordering heuristic

For a greenfield, multi-component build, order tasks by the dependency spine rather than by requirement section order:

1. **Scaffold + env** (layout, package manager, lint/type config) — unblocks every later verification command.
2. **Config/secrets** — needed by client, orchestration, and Compose.
3. **Infrastructure topology** (Compose) — can run in parallel with pure-code tasks; verify with a parse-only command (`docker compose config`).
4. **Contract before enforcement engine** — define the vendor-neutral contract first, then the GE suite that must cover it. This keeps the contract authoritative (the recurring 'contract is authority, engine enforces' pattern).
5. **Storage schema before writers** — DDL/table design before ingest logic.
6. **Client -> change detection -> idempotent load -> orchestration flow** — strict chain; each task's tests can use mocked transport until the integration task wires real infrastructure.
7. **Transformation models in grain order** — staging first, then natural-grain facts, then SCD2 (SCD2 depends on staging hash inputs).
8. **Orchestration/deployment glue** before **end-to-end integration test**, with **CI/README** last.

### Step 3b: Verification command selection rules

- Use parse-only commands (`dbt parse`, `docker compose config`) as the verification for config/model tasks; reserve `dbt build` and full `pytest` for the integration task. This keeps per-PR verification fast and hermetic.
- For a monorepo subdirectory project, scope every command with `uv run --directory <pkg>` (or the package manager's equivalent) so the command works from the repo root without `cd`.
- Chain ruff + mypy + the task's targeted test file; the CI task owns the full unsuffixed `pytest` run.

### Step 4a: Traceability check

Enumerate the requirements' numbered Acceptance Criteria and confirm each maps to at least one task `acceptance_criteria` entry. Record the mapping mentally (or in a comment) — the schema has no traceability field, so the only guarantee is an explicit manual pass over the AC list.

### Step 5a: Never trust `tasks-cli.py init` output

The `init` parser only recognizes headings matching `^###\s+(\d+)\.`. Requirements files that use `##` for major sections and `### N.M` for subsections produce duplicate IDs (e.g. four `TASK-005`) and acceptance criteria that bleed across section boundaries. Always:

1. Run `init` to create the scaffold, then immediately overwrite `.tasks/plan.json` with a hand-authored plan, OR skip init entirely and write the JSON directly.
2. Run `tasks-cli.py validate` to confirm schema validity (the CLI is the only sanctioned validator; writing files directly is allowed, but validation is mandatory).
3. Assert ID uniqueness across the task array — the schema does not enforce it, so duplicated IDs pass validation silently.

## Propose Learned Skill Patch
If the planning process revealed any generalizable patterns (e.g., effective task decomposition strategies, common dependency structures, or recurring requirement-to-task mappings), write a patch file to `.tasks/pending_skills/patch_<timestamp>.json` (max 15 KB). Do NOT edit live `.opencode/skills/` files directly.