#!/usr/bin/env python3
"""
OpenCode Skill Engine
Local host runner for validating, testing, and promoting proposed Hermes skill patches
from .tasks/pending_skills/ into active .opencode/skills/ or references/learned/.
"""

import sys
import os
import json
import shutil
import subprocess

MAX_SKILL_SIZE_BYTES = 15 * 1024  # 15 KB
MAX_TOOL_DESC_CHARS = 500
POLICY_FILE = ".opencode/policy.md"
PENDING_DIR = ".tasks/pending_skills"
SKILLS_DIR = ".opencode/skills"

def log_err(msg):
    print(f"❌ [Skill Engine Error]: {msg}", file=sys.stderr)

def log_ok(msg):
    print(f"✅ [Skill Engine]: {msg}")

def check_file_limits(file_path):
    size = os.path.getsize(file_path)
    if size > MAX_SKILL_SIZE_BYTES:
        log_err(f"File {file_path} exceeds size limit ({size} bytes > {MAX_SKILL_SIZE_BYTES} bytes).")
        return False
    return True

def verify_policy_integrity(patch_data):
    # Enforce immutable security rules
    content = json.dumps(patch_data).lower()
    forbidden_terms = ["ignore policy", "override policy", "rm -rf", "git reset --hard head~", "force push"]
    for term in forbidden_terms:
        if term in content:
            log_err(f"Forbidden policy override attempt detected: '{term}'")
            return False
    return True

def run_eval_suite(patch_path):
    cmd = [sys.executable, ".opencode/evals/eval_skills.py", "--patch", patch_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        log_err(f"Eval suite failed:\n{res.stderr}")
        return False
    log_ok("Eval suite passed.")
    return True

def promote_patch(patch_filename):
    patch_path = os.path.join(PENDING_DIR, patch_filename)
    if not os.path.exists(patch_path):
        log_err(f"Patch file {patch_path} not found.")
        sys.exit(1)

    if not check_file_limits(patch_path):
        sys.exit(1)

    with open(patch_path, "r", encoding="utf-8") as f:
        try:
            patch_data = json.load(f)
        except json.JSONDecodeError as e:
            log_err(f"Invalid JSON: {e}")
            sys.exit(1)

    if not verify_policy_integrity(patch_data):
        sys.exit(1)

    if not run_eval_suite(patch_path):
        sys.exit(1)

    target_skill = patch_data.get("target_skill")
    new_content = patch_data.get("content")

    if not target_skill or not new_content:
        log_err("Patch missing 'target_skill' or 'content' fields.")
        sys.exit(1)

    dest_path = os.path.join(SKILLS_DIR, target_skill)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    os.remove(patch_path)
    log_ok(f"Successfully promoted {patch_filename} to {dest_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: opencode-skill-engine <test|promote> [patch_filename]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "test" and len(sys.argv) >= 3:
        patch_path = sys.argv[2]
        if run_eval_suite(patch_path):
            log_ok(f"Test passed for {patch_path}")
            sys.exit(0)
        sys.exit(1)
    elif cmd == "promote" and len(sys.argv) >= 3:
        promote_patch(sys.argv[2])
    else:
        log_err("Invalid arguments.")
        sys.exit(1)

if __name__ == "__main__":
    main()