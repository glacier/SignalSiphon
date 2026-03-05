import streamlit as st
import asyncio
from signal_hydrator.adapters.graphql import GraphQLAdapter
from signal_hydrator.templating.jinja import JinjaHydrator
from signal_hydrator.langchain.template import HydratedPromptTemplate

st.set_page_config(page_title="Signal Hydrator Demo", layout="wide", page_icon="💧")

st.title("💧 Signal Hydrator - Zero-Latency Context Demo")
st.markdown("This interactive UI demonstrates how `signal-hydrator` parses a prompt template, fetches only the exact fields needed via GraphQL, and hydrates the prompt.")

# Mock Schema
schema_string = """
type Query { user(id: ID!): User }
type User { id: ID!, profile: Profile, orders: [Order] }
type Profile { name: String, email: String, tier: String }
type Order { id: ID!, total: Float, status: String }
"""

# Custom Adapter to capture the generated query for the UI
class UIDemoGraphQLAdapter(GraphQLAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_query = ""
        
    async def fetch(self, id: str, paths: list[str]) -> dict:
        self.last_query = self.build_query(paths)
        # Mock Response Data
        return {
            "profile": {"name": "Alice Skywalker", "tier": "Enterprise", "email": "alice@rebels.com"},
            "orders": [{"id": "ORD-12345", "total": 450.00, "status": "SHIPPED"}]
        }

# Sidebar settings
st.sidebar.header("Data Source Configuration")
st.sidebar.markdown("The underlying strict GraphQL Schema acting as the Backend.")
st.sidebar.code(schema_string, language="graphql")

# Main UI
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 📝 Write the Prompt Template")
    default_template = "You are assisting {{ user.profile.name }}. They are asking about their recent order: {{ user.orders[0].id }}. What is their tier: {{ user.profile.tier }}?"
    user_template = st.text_area("Jinja2 Template:", value=default_template, height=150)

    if st.button("🚀 Execute Hydration Pipeline", type="primary"):
        with st.spinner("Analyzing AST and executing network query..."):
            adapter = UIDemoGraphQLAdapter(
                endpoint="https://api.mock.com/graphql",
                schema_str=schema_string,
                root_type="User"
            )
            
            try:
                template = HydratedPromptTemplate(
                    template=user_template,
                    template_format="jinja2",
                    hydrator=JinjaHydrator(),
                    ext_adapters={"user": adapter}
                )
                
                # Run the asyncio formatting hook
                async def format_prompt():
                    return await template.aformat(user="user_777")
                    
                final_prompt = asyncio.run(format_prompt())
                st.session_state['final_prompt'] = final_prompt
                st.session_state['last_query'] = adapter.last_query
            except Exception as e:
                st.error(f"Error during hydration: {str(e)}")

with col2:
    st.subheader("2. 📡 Intercepted Network Query")
    if 'last_query' in st.session_state:
        st.markdown("*Instead of eagerly fetching the whole user, the library dynamically generated THIS exact GraphQL selection set:*")
        st.code(st.session_state['last_query'], language="graphql")
    else:
        st.info("Submit a prompt to see the generated AST query here.")

    st.subheader("3. 🤖 Final Hydrated Prompt")
    if 'final_prompt' in st.session_state:
        st.success(st.session_state['final_prompt'])
    else:
        st.info("The final LLM prompt will appear here.")
