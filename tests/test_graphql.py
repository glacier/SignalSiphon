import pytest
from signal_hydrator import GraphQLAdapter
from signal_hydrator.adapters.graphql import SchemaError

MOCK_SCHEMA = '''
type Profile {
    name: String!
    age: Int
}
type Organization {
    tier: String!
}
type Order {
    id: ID!
    total: Float!
}
type User {
    id: ID!
    profile: Profile!
    org: Organization!
    orders: [Order!]!
}
type Query {
    user(id: ID!): User
}
'''

def test_adapter_initializes_with_valid_schema():
    adapter = GraphQLAdapter(
        endpoint="http://localhost/graphql",
        schema_str=MOCK_SCHEMA,
        root_type="User"
    )
    assert adapter.root_type == "User"

def test_adapter_fails_on_invalid_schema():
    with pytest.raises(SchemaError):
        GraphQLAdapter(
            endpoint="http://localhost/graphql",
            schema_str="type Invalid { x: ",
            root_type="User"
        )

def test_adapter_fails_on_missing_root_type():
    with pytest.raises(SchemaError):
        GraphQLAdapter(
            endpoint="http://localhost/graphql",
            schema_str=MOCK_SCHEMA,
            root_type="Customer"
        )

def test_build_query():
    adapter = GraphQLAdapter(
        endpoint="http://localhost/graphql",
        schema_str=MOCK_SCHEMA,
        root_type="User"
    )
    
    paths = ["profile.name", "orders.[0].id"]
    query = adapter.build_query(paths)
    
    # Verify the generated query string contains the expected structure
    assert "query HydrateAgentContext($id: ID!) {" in query
    assert "user(id: $id) {" in query
    assert "profile" in query
    assert "name" in query
    assert "orders" in query
    assert "id" in query
