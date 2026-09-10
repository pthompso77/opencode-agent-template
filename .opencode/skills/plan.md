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
1. **Task**: Read `.tasks/requirements.md`.
2. **Act**: Analyze dependencies and break the work into ordered tasks (e.g., `TASK-001`, `TASK-002`).
3. **Verify**: Check that every requirement in `.tasks/requirements.md` maps to at least one task acceptance criterion.
4. **Execute**: Use the local CLI helper tool to generate/write `.tasks/plan.json`:
   `tasks-cli init --file .tasks/requirements.md`