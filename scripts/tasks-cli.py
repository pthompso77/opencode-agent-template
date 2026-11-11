#!/usr/bin/env python3
"""Atomic, schema-validated CLI for .tasks/plan.json state mutations.

Subcommands:
  update-status <task-id> --status <status>   Set a task's status (validated against plan.schema.json).
  validate                                    Validate .tasks/plan.json against .tasks/plan.schema.json.
  init --file <requirements.md>               Initialize .tasks/plan.json from a requirements file.
"""

import sys
import os
import json
import re

PLAN_PATH = ".tasks/plan.json"
SCHEMA_PATH = ".tasks/plan.schema.json"


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_schema():
    return _load_json(SCHEMA_PATH)


def allowed_statuses():
    schema = load_schema()
    try:
        return schema["properties"]["tasks"]["items"]["properties"]["status"]["enum"]
    except KeyError:
        return []


def validate_plan(data, schema=None):
    """Validate a plan document against the schema. Returns (ok, [errors])."""
    errors = []
    schema = schema or load_schema()

    if not isinstance(data, dict):
        return False, ["plan.json root must be an object"]

    for field in schema.get("required", []):
        if field not in data:
            errors.append(f"missing required field '{field}'")

    status_enum = schema["properties"]["tasks"]["items"]["properties"]["status"]["enum"]
    task_required = schema["properties"]["tasks"]["items"].get("required", [])

    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        errors.append("'tasks' must be an array")
        return False, errors

    for i, task in enumerate(tasks):
        for field in task_required:
            if field not in task:
                errors.append(f"task[{i}] missing required field '{field}'")
        status = task.get("status")
        if status is not None and status not in status_enum:
            errors.append(f"task[{i}] has invalid status '{status}' (allowed: {', '.join(status_enum)})")

    return (len(errors) == 0), errors


def _parse_tasks(requirements_text):
    """Decompose a requirements.md into ordered PR-sized tasks."""
    tasks = []

    # Split into numbered sections (e.g. "### 0. Title", "### 1. Title").
    sections = re.split(r"^###\s+", requirements_text, flags=re.MULTILINE)
    for section in sections[1:]:
        title_match = re.match(r"(\d+)\.\s*(.+)", section)
        if not title_match:
            continue
        num, title = title_match.groups()
        body = section[title_match.end():]

        criteria = re.findall(r"^\s*[-*]\s+(.+)$", body, flags=re.MULTILINE)

        tasks.append({
            "id": f"TASK-{int(num):03d}",
            "title": title.strip(),
            "status": "PENDING",
            "target_files": [],
            "verification_cmd": "",
            "acceptance_criteria": [c.strip() for c in criteria],
        })

    return tasks


def init_plan(requirements_path):
    with open(requirements_path, "r", encoding="utf-8") as f:
        text = f.read()

    tasks = _parse_tasks(text)
    if not tasks:
        print("No task sections found in requirements file.", file=sys.stderr)
        sys.exit(1)

    plan = {
        "version": "1.0",
        "current_phase": "PENDING",
        "tasks": tasks,
    }

    ok, errors = validate_plan(plan)
    if not ok:
        for e in errors:
            print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)

    with open(PLAN_PATH, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)
        f.write("\n")

    print(f"Initialized {PLAN_PATH} with {len(tasks)} tasks.")


def update_status(task_id, new_status):
    allowed = allowed_statuses()
    if new_status not in allowed:
        print(f"Error: invalid status '{new_status}'. Allowed: {', '.join(allowed)}", file=sys.stderr)
        sys.exit(1)

    with open(PLAN_PATH, "r+", encoding="utf-8") as f:
        data = json.load(f)
        found = False
        for task in data["tasks"]:
            if task["id"] == task_id:
                task["status"] = new_status
                found = True
                break
        if not found:
            print(f"Error: task '{task_id}' not found in {PLAN_PATH}.", file=sys.stderr)
            sys.exit(1)

        ok, errors = validate_plan(data)
        if not ok:
            for e in errors:
                print(f"Validation error: {e}", file=sys.stderr)
            sys.exit(1)

        f.seek(0)
        json.dump(data, f, indent=2)
        f.write("\n")
        f.truncate()

    print(f"Updated {task_id} status to {new_status}")


def _usage():
    print(__doc__)


def main():
    args = sys.argv[1:]
    if not args:
        _usage()
        sys.exit(1)

    cmd = args[0]

    if cmd == "update-status":
        # Parse: update-status <task-id> --status <status>
        if len(args) < 4 or args[2] != "--status":
            print("Usage: tasks-cli update-status <task-id> --status <status>", file=sys.stderr)
            sys.exit(1)
        update_status(args[1], args[3])

    elif cmd == "validate":
        data = _load_json(PLAN_PATH)
        ok, errors = validate_plan(data)
        if not ok:
            for e in errors:
                print(f"Validation error: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"{PLAN_PATH} is valid.")

    elif cmd == "init":
        if len(args) < 3 or args[1] != "--file":
            print("Usage: tasks-cli init --file <requirements.md>", file=sys.stderr)
            sys.exit(1)
        init_plan(args[2])

    else:
        _usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
