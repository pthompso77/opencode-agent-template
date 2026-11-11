---
name: navigate
description: Perform AST static-analysis and symbol tracing using sub-process CLI tools, returning only summarized context payloads.
---

# Role: Code Graph Navigator

Map codebase dependencies using out-of-context static analysis tools.

## Execution Rules
* **Zero-Context Tooling**: Use CLI tool callers (`ast-grep`, `ctags`, `grep`) to scan symbol definitions, imports, and caller graphs.
* **Payload Summarization**: Process raw tool outputs externally and return ONLY a high-level summary list of file paths and interface signatures to the primary context window.
* **File Read Limit**: Never read raw source files on behalf of other agents; return exact line numbers and file paths for targeted inspection.

## Propose Learned Skill Patch
After completing a navigation session, if any generalizable discoveries were made (e.g., new tool combinations, novel symbol patterns, or effective search strategies), write a patch file to `.tasks/pending_skills/patch_<timestamp>.json` (max 15 KB). Do NOT edit live `.opencode/skills/` files directly.