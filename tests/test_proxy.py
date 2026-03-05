from signal_hydrator.runtime.proxy import ContextProxy
import pytest

def test_proxy_records_paths_without_fetching():
    # A dummy mock adapter that we ensure doesn't actually get called
    class MockAdapter:
        def fetch(self, id, paths):
            raise Exception("Adapter fetch should not be called synchronously by a Proxy!")

    proxy = ContextProxy(id="123", adapter=MockAdapter())
    
    # Access deeply nested properties
    _ = proxy.profile.name
    _ = proxy.orders[0].id
    
    # The proxy should internally track these paths
    recorded_paths = proxy._get_pending_paths()
    
    # Order doesn't matter, but it should contain both
    assert "profile.name" in recorded_paths
    assert "orders[0].id" in recorded_paths
