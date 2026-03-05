import pytest
import asyncio
from typing import List, Dict, Any
from signal_hydrator.runtime.dataloader import AsyncDataLoader
from signal_hydrator.runtime.proxy import ContextProxy
from signal_hydrator.adapters.base import SignalAdapter

class MockAdapter(SignalAdapter):
    def __init__(self):
        self.call_count = 0
        self.last_paths = []
        
    @property
    def root_type(self) -> str:
        return "User"
        
    async def fetch(self, id: str, paths: List[str]) -> Dict[str, Any]:
        self.call_count += 1
        self.last_paths = paths
        return {"profile": {"name": "Test User"}, "org": {"tier": "Enterprise"}}

@pytest.mark.asyncio
async def test_dataloader_batches_requests():
    adapter = MockAdapter()
    loader = AsyncDataLoader()
    
    # 1. Provide a proxy to the "LLM"
    proxy = ContextProxy(id="123", adapter=adapter)
    
    # 2. Simulate an LLM synchronously accessing fields in a tight loop
    _ = proxy.profile.name
    _ = proxy.org.tier
    _ = proxy.orders[0].id
    
    # At this exact moment, adapter should NOT be called yet
    assert adapter.call_count == 0
    
    # 3. Queue the proxy into the loader and await resolution
    # By yielding to the event loop, the loader should batch the recorded paths so far
    result = await loader.load(proxy)
    
    # 4. Verify the adapter was called exactly ONCE with all 3 paths
    assert adapter.call_count == 1
    assert "profile.name" in adapter.last_paths
    assert "org.tier" in adapter.last_paths
    assert "orders[0].id" in adapter.last_paths
    
    # 5. Verify it returned the dictionary correctly
    assert result["profile"]["name"] == "Test User"
