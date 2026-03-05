import asyncio
from signal_siphon.adapters.graphql import GraphQLAdapter
from signal_siphon.templating.jinja import JinjaHydrator
from signal_siphon.langchain.template import HydratedPromptTemplate

# 1. Define a strict GraphQL schema
schema_string = """
type Query {
  user(id: ID!): User
}
type User {
  id: ID!
  profile: Profile
  orders: [Order]
}
type Profile {
  name: String
  email: String
  tier: String
}
type Order {
  id: ID!
  total: Float
}
"""

class MockGraphQLAdapter(GraphQLAdapter):
    """A mock GraphQL adapter that just prints the generated AST Query instead of making a real network request."""
    async def fetch(self, id: str, paths: list[str]) -> dict:
        # Build the exact GraphQL query string the library generated
        query = self.build_query(paths)
        print("\n--- 📡 NETWORK INTERCEPT ---")
        print("Instead of sending a massive JSON blob, signal-siphon generated THIS tiny, exact GraphQL query:")
        print(f"\n{query}")
        print("----------------------------\n")
        
        # Return mock data as if the server responded
        return {
            "profile": {"name": "Alice Skywalker", "tier": "Enterprise"},
            "orders": [{"id": "ORD-12345"}]
        }

async def main():
    print("🤖 Agent is preparing to execute a prompt...")
    
    # 2. Configure the adapter
    adapter = MockGraphQLAdapter(
        endpoint="https://api.mock.com/graphql",
        schema_str=schema_string,
        root_type="User"
    )

    # 3. Create the LangChain template
    # Notice we ask for exactly TWO specific nested things: `profile.name` and `orders[0].id`
    template = HydratedPromptTemplate(
        template="You are assisting {{ user.profile.name }}. They are asking about their recent order: {{ user.orders[0].id }}. What is their tier: {{ user.profile.tier }}?",
        template_format="jinja2",
        hydrator=JinjaHydrator(),
        ext_adapters={"user": adapter}
    )

    # 4. Format the prompt (this triggers the invisible AST scan and network fetch)
    print("⏳ Calling `.aformat(user='user_777')`...")
    final_prompt = await template.aformat(user="user_777")
    
    print("✅ Final Prompt delivered to the LLM:")
    print(f"   ► {final_prompt}")

if __name__ == "__main__":
    asyncio.run(main())
