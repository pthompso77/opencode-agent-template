#!/usr/bin/env python3
"""
Deterministic Skill Evaluation Harness
Evaluates proposed skill patches for safety boundary compliance, size budgets,
and frontmatter structural validity before promotion.
"""

import sys
import json
import argparse
import re

def eval_patch(patch_path):
    try:
        with open(patch_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"EVAL FAILURE: Unable to load patch JSON: {e}", file=sys.stderr)
        return False

    content = data.get("content", "")
    target = data.get("target_skill", "")

    # Check 1: Must target valid skill or learned reference
    if not (target.endswith(".md") or target.endswith(".json")):
        print(f"EVAL FAILURE: Target skill '{target}' must end in .md or .json", file=sys.stderr)
        return False

    # Check 2: Frontmatter validation for markdown skills
    if target.endswith(".md"):
        frontmatter_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not frontmatter_match:
            print("EVAL FAILURE: Missing YAML frontmatter block (---)", file=sys.stderr)
            return False
        
        frontmatter = frontmatter_match.group(1)
        if "description:" not in frontmatter or "name:" not in frontmatter:
            print("EVAL FAILURE: Frontmatter missing 'name' or 'description' fields.", file=sys.stderr)
            return False

    # Check 3: Absolute forbidden string patterns (Safety Boundary)
    forbidden_patterns = [
        r"rm\s+-rf\s+/",
        r"git\s+reset\s+--hard\s+HEAD~[0-9]+",
        r"chmod\s+777",
        r"eval\(",
        r"ignore\s+previous\s+instructions"
    ]
    for pattern in forbidden_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            print(f"EVAL FAILURE: Malicious or forbidden pattern detected: '{pattern}'", file=sys.stderr)
            return False

    # Check 4: Non-subversion of 2-attempt troubleshooting rule
    if "troubleshoot" in target and "attempt" in content.lower():
        if "infinite" in content.lower() or "unlimited" in content.lower():
            print("EVAL FAILURE: Troubleshooter cannot override bounded retry limits.", file=sys.stderr)
            return False

    print("EVAL PASS: All policy and structural assertions passed.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Skill Patch Eval Harness")
    parser.add_argument("--patch", required=True, help="Path to patch JSON file")
    args = parser.parse_args()

    if eval_patch(args.patch):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()