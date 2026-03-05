import pytest
from signal_siphon.adapters.rest import RESTAdapter
import httpx

class MockResponse:
    def __init__(self, json_data):
        self._json_data = json_data
        
    def json(self):
        return self._json_data

    def raise_for_status(self):
        pass

@pytest.mark.asyncio
async def test_rest_adapter_heuristic_fetching(monkeypatch):
    """
    Tests that the REST adapter uses the first segment of the path 
    to guess the sub-resource endpoint.
    e.g., "orders[0].id" should trigger a fetch to `/users/123/orders`
    """
    
    fetched_urls = []
    
    async def mock_get(self, url, *args, **kwargs):
        fetched_urls.append(url)
        if url.endswith("/users/123"):
            return MockResponse({"id": "123", "profile": {"name": "Test"}})
        elif url.endswith("/users/123/orders"):
            return MockResponse([{"id": "A1"}, {"id": "A2"}])
        return MockResponse({})

    # Patch the async client GET method
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    
    adapter = RESTAdapter(
        base_url="https://api.example.com",
        root_resource="users"
    )
    
    # We ask for the root profile name, and an order's ID
    paths = ["profile.name", "orders[0].id"]
    
    data = await adapter.fetch(id="123", paths=paths)
    
    # Verify the two distinct endpoints were hit
    assert "https://api.example.com/users/123" in fetched_urls
    assert "https://api.example.com/users/123/orders" in fetched_urls
    
    # Verify the data was stitched together correctly into a single root dict
    assert data["profile"]["name"] == "Test"
    assert data["orders"][0]["id"] == "A1"
