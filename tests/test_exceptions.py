import pytest
from httpx import HTTPStatusError, RequestError, Response, Request
from signal_hydrator.adapters.graphql import GraphQLAdapter
from signal_hydrator.exceptions import AdapterFetchError, GraphQLError

MOCK_SCHEMA = '''
type Profile { name: String! }
type User { id: ID!, profile: Profile! }
type Query { user(id: ID!): User }
'''

class MockHTTPStatusErrorClient:
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc_val, exc_tb): pass
    async def post(self, *args, **kwargs):
        req = Request("POST", "http://test")
        resp = Response(500, request=req)
        raise HTTPStatusError("500 Server Error", request=req, response=resp)

class MockRequestErrorClient:
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc_val, exc_tb): pass
    async def post(self, *args, **kwargs):
        req = Request("POST", "http://test")
        raise RequestError("Connection Timeout", request=req)

class MockGraphQLErrorClient:
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc_val, exc_tb): pass
    async def post(self, *args, **kwargs):
        class MockResponse:
            def raise_for_status(self): pass
            def json(self):
                return {"errors": [{"message": "Cannot query field 'fake' on type 'Profile'."}]}
        return MockResponse()

@pytest.mark.asyncio
async def test_graphql_adapter_raises_http_status_error(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", lambda: MockHTTPStatusErrorClient())
    adapter = GraphQLAdapter(endpoint="http://localhost", schema_str=MOCK_SCHEMA, root_type="User")
    with pytest.raises(AdapterFetchError, match="HTTP error fetching GraphQL data: 500"):
        await adapter.fetch("123", ["profile.name"])

@pytest.mark.asyncio
async def test_graphql_adapter_raises_request_error(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", lambda: MockRequestErrorClient())
    adapter = GraphQLAdapter(endpoint="http://localhost", schema_str=MOCK_SCHEMA, root_type="User")
    with pytest.raises(AdapterFetchError, match="Network error fetching GraphQL data"):
        await adapter.fetch("123", ["profile.name"])

@pytest.mark.asyncio
async def test_graphql_adapter_raises_graphql_error(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", lambda: MockGraphQLErrorClient())
    adapter = GraphQLAdapter(endpoint="http://localhost", schema_str=MOCK_SCHEMA, root_type="User")
    with pytest.raises(GraphQLError, match="GraphQL returned validation or execution errors.") as excinfo:
        await adapter.fetch("123", ["profile.name"])
    assert excinfo.value.errors[0]["message"] == "Cannot query field 'fake' on type 'Profile'."
