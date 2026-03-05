# Signal Hydrator Agent Instructions

This repository is maintained with the help of AI coding agents. If you are an AI assistant contributing to this project, you must adhere to the following open-source development standards.

## 1. Test-Driven Development (TDD)
- Write tests *before* implementing new features or fixing bugs.
- Ensure all tests pass using `pytest` before considering a task complete.
- Test coverage must remain high. When adding a new Adapter or feature, build comprehensive test suites for it.
- Use `pytest-asyncio` for all asynchronous code.

## 2. Code Quality & Standards
- Follow PEP 8 style guidelines.
- Add type hints to all function signatures (`typing` module) to maintain strict typing.
- Provide descriptive docstrings for all classes and public methods. Keep them concise but informative.
- Keep dependencies minimal. Only add new dependencies to `pyproject.toml` if absolutely necessary and clearly justified.

## 3. Git Workflow
- Always try to make atomic, logical commits. Avoid giant commits that touch unrelated areas.
- Use conventional commit messages: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`.
- Include a clear description in the commit message if the change is complex.

## 4. Documentation
- If you change public APIs or add new features, you **must** update `README.md` to reflect the changes.
- Ensure examples in the README remain functional.
- Maintain the `ROADMAP.md` and `task.md` if working iteratively across larger phases.

## 5. Architectural Integrity
- Follow the established two-paradigm design: Prompt-Time Hydration (via AST scanning) and Runtime Hydration (via Proxies and DataLoaders).
- Do not introduce breaking changes to the `SignalAdapter` interface without major version bumps.
- `signal-hydrator` integrates optionally with LangChain. Features that depend on LangChain must handle `ImportError` gracefully so the core library remains framework-agnostic.
