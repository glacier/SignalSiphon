# signal-siphon

A zero-latency, lazy-loading context hydrator for AI agents.

Stop eagerly fetching massive context payloads for your LLMs. `signal-siphon` intelligently parses your agent prompts and fetches exactly the fields requested—nothing more, nothing less. 

## Installation
```bash
pip install signal-siphon
```

For native LangChain and LangGraph support:
```bash
pip install "signal-siphon[langchain]"
```

## Features

- **AST Prompt Scanning:** Parses Jinja2 templates before rendering to discover exactly which dot-notation paths your LLM needs.
- **Runtime Proxy DataLoader:** Injects a magic `ContextProxy` into your agent execution environment that defers network requests and batches them seamlessly.
- **Adapter Ecosystem:** Pluggable backends for strictly-typed GraphQL servers, heuristic REST APIs, and direct SQL databases.
- **Zero Over-fetching:** By combining requested paths like `["profile.name", "orders[0].id"]` into a single, optimized backend query, your context window remains pristine and your N+1 tool-calling problems vanish.

## Quickstart (Prompt-Time Hydration)

The easiest way to integrate the library is with LangChain's native templating.

```python
from signal_siphon import HydratedPromptTemplate, GraphQLAdapter, JinjaHydrator

# 1. Define your strict data source
adapter = GraphQLAdapter(
    endpoint="https://api.example.com/graphql",
    schema_string="type User { profile: Profile } ...",
    root_type="User"
)

# 2. Wrap your standard LangChain template
template = HydratedPromptTemplate.from_template(
    template="Hello {{ user.profile.name }}, your order ID is {{ user.orders[0].id }}.",
    template_format="jinja2",
    hydrator=JinjaHydrator(),
    ext_adapters={"user": adapter}
)

# 3. Use it like normal! The network fetch is entirely invisible.
# The hydrator scans the AST, finds the two paths, makes ONE graphql query, and renders.
final_prompt = await template.aformat(user="user_123")
```

## Advanced: Runtime Hydration (DataLoader)

For Python execution environments where prompts are completely dynamic, use the `ContextProxy` and `AsyncDataLoader`.

```python
from signal_siphon import ContextProxy, AsyncDataLoader, RESTAdapter

# 1. Provide an adapter (e.g. Heuristic REST)
adapter = RESTAdapter(base_url="https://api.example.com", root_resource="users")

# 2. Inject a magic proxy into your execution environment.
# Accessing properties on this proxy does NOT block or execute network requests!
proxy = ContextProxy(id="user_123", adapter=adapter)

# 3. Simulate Agent dynamic interaction
_ = proxy.profile.name
_ = proxy.orders[0].id

# 4. Batch everything into ONE network request and hydrate it
loader = AsyncDataLoader()
hydrated_data = await loader.load(proxy)
```

## LangGraph & Tools

Expose your adapters directly to your agents using native LangChain tools.

```python
from signal_siphon import HydratorTool, RESTAdapter

adapter = RESTAdapter(base_url="https://api.mycompany.com", root_resource="users")

# Dynamically generates a Pydantic args_schema based on the adapter
tool = HydratorTool.from_adapter(adapter)

# Pass it directly to your LCEL chain or LangGraph
llm_with_tools = llm.bind_tools([tool])
```

## Supported Adapters

`signal-siphon` supports expanding backends out of the box:

- **GraphQLAdapter:** Translates dot-paths into optimized GraphQL selection sets (Requires `graphql-core`).
- **RESTAdapter:** Heuristically builds root (`/users/1`) and sub-resource (`/users/1/orders`) endpoints by parsing paths.
- **SQLAdapter (Experimental):** Translates deep path requests directly into SQL `SELECT ... LEFT JOIN` queries.

```python
from signal_siphon import SQLAdapter

adapter = SQLAdapter(connection_string="sqlite:///:memory:", root_table="users")
# Path ["orders[0].id"] translates to:
# SELECT orders.id FROM users LEFT JOIN orders ON orders.users_id = users.id WHERE users.id = '123';
```
