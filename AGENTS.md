# AGENTS.md

> **Notice to AI Agents:** This document defines the technical constraints, architectural patterns, and development standards for this repository. Adhere to these guidelines strictly when generating code, refactoring, or suggesting improvements.

---

## 1. Technical Stack & Environment
* **Runtime:** Python 3.10+ (Prefer 3.12 syntax where possible).
* **Package Management:** `uv` is the primary tool for environment and dependency management.
* **Type System:** Strict `mypy` compliance. Use `from __future__ import annotations` for forward references.
* **Linting/Formatting:** `ruff` (Use `ruff check --fix` and `ruff format`).

## 2. Architectural Principles
* **Functional Core, Imperative Shell:** Keep business logic pure and side-effect free.
* **Dependency Injection:** Avoid global state. Inject services and configurations into class constructors or function arguments.
* **Async by Default:** For I/O bound operations, prioritize `asyncio`. Use `AnyIO` if the library needs to support multiple backends.
* **Minimalism:** Do not introduce third-party dependencies for functionality that exists in the Python Standard Library (e.g., use `pathlib` over `os.path`).

## 3. Coding Standards for Agents
### A. Type Safety
* All public functions **must** have return type annotations.
* Use `Optional` or `| None` for nullable fields.
* Leverage `TypedDict` for complex dictionary structures or `Pydantic` models for data validation.

### B. Documentation & Context
* **Docstrings:** Use Google Style docstrings.
* **Inline Comments:** Explain the "Why," not the "What."
* **Self-Correction:** If you identify a violation of these standards in existing code while performing a task, highlight it for refactoring.

### C. Error Handling
* Define domain-specific exceptions in `src/[package]/exceptions.py`.
* Use `ExceptionGroup` for handling multiple concurrent failures in async code.
* Avoid "Pokémon" exception handling (`except Exception: pass`).

## 4. Testing & Quality Assurance
* **Framework:** `pytest` with `pytest-asyncio` for asynchronous tests.
* **Philosophy:** Aim for 90%+ coverage on the `core/` logic. 
* **Mocking:** Use `unittest.mock` or `pytest-mock`. Ensure mocks accurately reflect the interface of the object being mocked.
* **Property-Based Testing:** Consider `hypothesis` for complex data validation logic.

## 5. Agent-Specific Context
* **Context Window Management:** When suggesting large refactors, provide a summary of changes first to ensure alignment before generating the full diff.
* **Naming Conventions:** * Variables/Functions: `snake_case`
    * Classes: `PascalCase`
    * Constants: `UPPER_SNAKE_CASE`
    * Private members: `_leading_underscore`

---

## How to use this file
1. **Initialize:** Start every session by reading this file.
2. **Validate:** Before submitting a code block, verify it follows the **Linting** and **Type Safety** sections.
3. **Report:** If project requirements conflict with these standards, ask for clarification.
