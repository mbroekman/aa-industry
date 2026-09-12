# Python AI Agent Guidelines

**Core Directive:** Write robust, highly optimized, and clean Python code. Prioritize maintainability and algorithmic efficiency without unnecessary technical debt. Use established libraries over reinventing the wheel.

## 1. Task Management via `backlog-md` Tool

* **Task Registration First:** Whenever you receive a new assignment, feature request, or bug report, you **MUST FIRST** execute the `backlog-md` tool to convert the request into actionable technical tasks before writing or modifying any code.
* **Task Creation for Session Continuity:** Always create a detailed Backlog task before starting work. Record investigation findings, acceptance criteria, and plan steps in the task so fresh sessions can immediately read up on full context.
* **Temporary Files Cleanup:** Always remove temporary debug or test scripts after use to keep the repository clean.
* **Always Run Tests Before Completing:** You must at all times first run the tests to verify correctness before reporting any task or feature as done.
* **Tool Workflow:**
    1. **Read:** Execute the tool to read the current backlog and determine the next priority.
    2. **Create:** Pass the parsed user request to the `backlog-md` tool to generate new tasks.
    3. **Update:** Use the tool to update the status of a task to Work-In-Progress (WIP) before starting development.
    4. **Complete:** Use the tool to mark a task as Done **only** after all code is written, tested, type-checked, and linted.
* **Strict Compliance:** **NEVER** execute code changes for a feature, refactor, or bugfix that has not been formally registered and tracked via the `backlog-md` tool.

## 2. Tooling & Environment

* **Package Management:** Use `uv` exclusively (including `.venv` creation). Document in `pyproject.toml`.
* **Formatting & Linting:** Use `Ruff` (max 88 chars, strict PEP 8). No wildcard imports.
* **Type Checking:** Use `mypy` strictly. No `Any` unless unavoidable.
* **Testing:** Use `pytest`. Mock external dependencies. Do not run generated tests without saving to a discrete, `.gitignore`d file first.
* **Data Science:** Use `polars` (never `pandas`). Ingest max 50 rows (e.g., `df.sample(50)`) for context. Never print dataframe schema and length simultaneously.
* **Notebooks:** Ensure `ipykernel` and `ipywidgets` are installed. Use `tqdm` for long loops. Explicitly `print()` DataFrames in conditional blocks.

## 3. Code Standards & Architecture

* **Naming:** snake_case (vars/funcs), PascalCase (classes), UPPER_CASE (constants). No emojis or unicode equivalents.
* **Functions:** Single responsibility, max 5 parameters, return early. **Never** use mutable default arguments.
* **Classes:** Prefer composition over inheritance. Use `@property` for computed attributes and `dataclasses` for simple structures.
* **Best Practices:** Use f-strings, context managers (`with`), list comprehensions, and `is` for None/Booleans.

## 4. Optimization & Data Handling

* Maximize Big-O efficiency for memory and runtime. Implement vectorization where appropriate.
* **Databases:** Do not denormalize unless requested. Use precise types (e.g., `TIMESTAMP`). Use `ARRAY` for nested fields, never `TEXT/STRING`.
* **Benchmarking:** Never run in parallel. Do not manipulate tests to pass constraints. Disable caching if testing independent performance.

## 5. Error Handling & Security

* **Security:** Never store or log secrets, API keys, or PII. Use `.env` (ensure it is `.gitignore`d) and environment variables.
* **Exceptions:** No bare `except:` clauses. Catch specific exceptions. Log errors using `logger.error` (not `print`).
* **Comments/Docs:** Docstrings required for all public functions/classes (include args, returns, raises). Do not write self-evident or tautological comments.

## 6. Pre-Commit Checklist (Internal Agent Verification)

Before finalizing output, verify:

1. All tasks are correctly updated via `backlog-md`.
2. All tests and type checks (mypy) pass.
3. Ruff formatting is applied.
4. No hardcoded credentials, debug prints, or commented-out code exist.
5. If a new `@shared_task` was added: the README `CELERYBEAT_SCHEDULE` block is updated in the **same commit**.
6. **Documentation Updates (MANDATORY)**: Always proactively update `CHANGELOG.md` and any relevant user manuals (e.g., `user_manual_en.md`) or architecture docs in `backlog/docs/` after completing features or bug fixes, **before** closing the task.

## 7. Project-Specific Conventions

### Celery Tasks
- Every new `@shared_task` **must** be added to the `CELERYBEAT_SCHEDULE` block in `README.md` in the **same commit** as the task itself.
- Task names follow the pattern `<app_name>.tasks.<function_name>` — keep this consistent with the `name=` argument on the decorator.
- Never ship a task that has no schedule documented in the README. This causes silent failures during fresh installs.
- **Helper tasks** (tasks with required positional arguments, e.g. `resolve_unknown_locations(location_ids)`) must **NOT** be added to `CELERYBEAT_SCHEDULE`. They are called by other tasks with arguments and cannot run standalone. Only add tasks with no required arguments to the schedule.

### Templates
- DataTables `colspan` in `{% empty %}` rows must match the exact number of `<th>` columns in the corresponding `<thead>`. Mismatch causes DataTables error TN/18.
- DataTables `columnDefs` target indices are 0-based; verify against the actual column count after any column addition or removal.
