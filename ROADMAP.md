# Signal Hydrator Roadmap & Implementation Spec

## Vision
To provide a zero-latency, lazy-loading context middle-layer for AI Agents. Agents should be able to traverse deeply nested, complex user contexts without eagerly "over-fetching" massive JSON payloads and without suffering the "N+1 Problem" of sequential LLM tool-calling.

## Core Paradigms

1. **Prompt-Time Hydration (The "AST Scanner")**
   - *Use Case:* Static template strings (like Jinja2) that define context before hitting the LLM.
   - *Mechanic:* An Abstract Syntax Tree (AST) scanner reads the template, extracts the exact required dot-notation paths (e.g., `user.profile.name`), and compiles them into a single, highly-optimized network query before rendering.

2. **Runtime Hydration (The "DataLoader")**
   - *Use Case:* Dynamic agent execution (like Python Code Interpreters) or dynamic LLM tool-calling.
   - *Mechanic:* Agents are given a `Proxy` representation of their context variables. Property accesses (e.g., `user.orders[0].id`) are added to a pending queue. An `asyncio` event-loop DataLoader batches the entire queue on the next tick into a single network query.

---

## Phase 1: The Core Architecture (v0.1) [COMPLETED]

The foundation of the library, focusing exclusively on **Prompt-Time Hydration**.

*   [x] **Project Scaffolding:** `pyproject.toml` with `pydantic`, `graphql-core`, and `jinja2`.
*   [x] **Adapter Interface:** Define `SignalAdapter` ABC handling `fetch(id: str, paths: List[str])`.
*   [x] **GraphQL Adapter:**
    *   Initialize with strict GraphQL Schema validation.
    *   Parse dot-notation paths from AST scanners.
    *   Compile paths into a single `graphql-core` SelectionSet AST.
    *   Execute single query via `httpx`.
*   [x] **Jinja Hydrator Engine:**
    *   Compile Jinja2 templates to AST.
    *   Traverse AST looking for `Getattr` on context root variables.
    *   Extract deeply nested paths while pruning generic/intermediate prefixes.
*   [x] **LangChain Integration:**
    *   Implement `HydratedPromptTemplate` extending LangChain's native `PromptTemplate`.
    *   Enable automatic, invisible network fetching during standard `.aformat()` calls.
*   [x] **Testing:** Robust `pytest` suite for schema validation, path pruning, and query generation.

---

## Phase 2: The Runtime Engine (DataLoader)

Focusing on dynamic environments where the prompt or script isn't known ahead of time.

*   [ ] **The Context Proxy:**
    *   Implement Python `__getattr__` or `__getitem__` hooks on a dummy `ContextObject`.
    *   Instead of returning real data, accessing `user.profile` returns a pending future/promise.
*   [ ] **The DataLoader Batcher:**
    *   Implement an `asyncio`-aware request queue.
    *   As the LLM script asynchronously access 50 `Proxy` paths in a loop, queue them without triggering a network request.
*   [ ] **Event-Loop Synchronization:**
    *   Use `loop.call_soon()` to yield execution and detect the end of the current CPU tick.
    *   Batch all queued paths into the registered `SignalAdapter`.
*   [ ] **LangChain Tool Integration:**
    *   Implement `HydratorTool.from_adapter()`.
    *   Given a `GraphQLAdapter`, dynamically construct a Pydantic `args_schema` that strictly matches the remote server's schema.
    *   Registers as a native LangGraph node tool for immediate use by LLMs.

---

## Phase 3: Adapter Expansion

Expanding beyond native GraphQL.

*   [ ] **The REST Adapter (Heuristic):**
    *   Handle legacy APIs where field selection isn't possible.
    *   Implement fetching logic bounded by root resources (e.g., `user.profile.name` fetches `GET /users/1`).
    *   Implement path traversal deduction (e.g., `user.orders` fetches `GET /users/1/orders`).
*   [ ] **The SQL/ORM Adapter (Experimental):**
    *   Allow direct connections to databases (Postgres/MySQL) via SQLAlchemy.
    *   Turn requested paths directly into optimized SQL `SELECT` field statements with `JOIN` clauses.

---

## Phase 4: Production Polish

Ensuring enterprise readiness.

*   [ ] **Caching Layer:** Implement LRU caching or Redis integration to prevent re-fetching the same paths across a multi-turn LangGraph conversation.
*   [ ] **Telemetry & Observability:** Integrate OpenTelemetry/LangSmith tracing to show developers exactly how many tokens they saved via field pruning.
*   [ ] **Documentation Site:** Launch a MkDocs site with guides for LangChain, LlamaIndex, and raw Jinja deployments.
