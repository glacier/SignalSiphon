import asyncio
from typing import Dict, Any
from signal_hydrator.runtime.proxy import ContextProxy

class AsyncDataLoader:
    """
    Batches proxy accesses and executes them in a single event-loop tick.
    """
    def __init__(self):
        # We don't implement full tick-level automatic batching in v0.2.
        # Instead, we implement an explicit `await loader.load(proxy)` which
        # extracts all pending paths synchronously accessed *up to this line*,
        # and executes them as one network request.
        pass

    async def load(self, proxy: ContextProxy) -> Dict[str, Any]:
        """
        Takes a ContextProxy, reads all recorded dot-paths, and resolves them
        via the proxy's configured Adapter.
        """
        paths = proxy._get_pending_paths()
        if not paths:
            return {}
            
        adapter = proxy.__dict__["_adapter"]
        id_val = proxy.__dict__["_id"]
        
        # Execute the single batched request
        hydrated_data = await adapter.fetch(id=id_val, paths=paths)
        
        return hydrated_data
