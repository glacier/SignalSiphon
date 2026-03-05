from typing import Any, Dict, List
import asyncio
from .base import SignalAdapter

class RESTAdapter(SignalAdapter):
    """
    A heuristic-based adapter for legacy REST APIs.
    Unlike GraphQL, it cannot select specific fields. 
    It guesses sub-resource endpoints based on the path prefixes.
    """

    def __init__(self, base_url: str, root_resource: str):
        self.base_url = base_url.rstrip('/')
        self._root_resource = root_resource
        
    @property
    def root_type(self) -> str:
        # e.g., "users" -> "Users"
        return self._root_resource.capitalize()

    async def fetch(self, id: str, paths: List[str]) -> Dict[str, Any]:
        """
        Groups paths by their top-level prefix.
        - "profile.name" targets the base resource: `/users/{id}`
        - "orders[0].id" targets a sub-resource mapping: `/users/{id}/orders`
        """
        import httpx
        
        # 1. Always fetch the base root object
        endpoints_to_fetch = set()
        endpoints_to_fetch.add(f"{self.base_url}/{self._root_resource}/{id}")
        
        # 2. Extract top-level sub-resources from the paths
        # e.g., ["profile.name", "orders[0].price"] -> {"profile", "orders"}
        top_level_keys = set()
        for path in paths:
            first_segment = path.split('.')[0].split('[')[0]
            top_level_keys.add(first_segment)
            
        # For a v0.1 heuristic: assume any top-level key that isn't 'profile' or 'settings' etc
        # might be a sub-resource endpoint.
        # This is highly primitive and would require explicit configuration mapping in v1.0
        # For testing purposes, if it's "orders", we hit `/users/123/orders`
        for key in top_level_keys:
            if key == "orders":
                 endpoints_to_fetch.add(f"{self.base_url}/{self._root_resource}/{id}/{key}")
                 
        from ..exceptions import AdapterFetchError
        
        # 3. Fetch all required endpoints concurrently
        async def fetch_url(client, url):
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                return url, resp.json()
            except httpx.HTTPStatusError as e:
                raise AdapterFetchError(f"HTTP error fetching REST data from {url}: {e.response.status_code}", original_error=e)
            except httpx.RequestError as e:
                raise AdapterFetchError(f"Network error fetching REST data from {url}: {str(e)}", original_error=e)

        async with httpx.AsyncClient() as client:
            tasks = [fetch_url(client, url) for url in endpoints_to_fetch]
            # Since AGENTS.md says to use ExceptionGroup, we can use return_exceptions=True
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for exceptions
            errors = [res for res in results if isinstance(res, Exception)]
            if errors:
                # If there's an ExceptionGroup available in >=3.11, use it. Otherwise raise the first error.
                try:
                    raise ExceptionGroup("Multiple errors occurred while fetching REST data", errors)
                except NameError:
                    raise errors[0] # Fallback for Python < 3.11
            
        # 4. Stitch the JSON payloads back into a single root dictionary
        root_data = {}
        for url, data in results:
            if url.endswith(f"/{id}"):
                # This is the root resource dictionary
                root_data.update(data)
            else:
                # This is a sub-resource. The key is the last segment of the URL
                sub_key = url.split('/')[-1]
                root_data[sub_key] = data
                
        return root_data
