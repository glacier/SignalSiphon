from typing import Type, Any, Optional
from pydantic import BaseModel, create_model, Field
from signal_siphon.adapters.base import SignalAdapter

try:
    from langchain_core.tools import BaseTool
except ImportError:
    # If langchain isn't installed, fallback to a basic Pydantic BaseModel
    # so that the cls(name=..., description=...) constructor still works
    class BaseTool(BaseModel):
        name: str
        description: str
        args_schema: Any

class HydratorTool(BaseTool):
    """
    A LangChain Tool that wraps a SignalAdapter.
    It takes an ID and a list of path strings (e.g., ["profile.name", "orders[0].id"])
    and returns the explicitly hydrated dictionary.
    """
    
    # We use __fields__ or explicitly redefine them for BaseTool compatibility
    name: str
    description: str = "Hydrates missing context fields dynamically"
    args_schema: Type[BaseModel]
    
    # Needs to be passed but hidden from pydantic fields
    _adapter: SignalAdapter = ...

    def _run(self, id: str, paths: list[str]) -> Any:
        """Synchronous run is not recommended as adapters perform I/O."""
        import asyncio
        # We try to grab the current loop, if none, we create one
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            raise RuntimeError("Cannot run synchronous tool inside an async loop. Use async tool-calling.")
            
        return loop.run_until_complete(self._adapter.fetch(id=id, paths=paths))

    async def _arun(self, id: str, paths: list[str]) -> Any:
        """The standard async fetch behavior."""
        return await self._adapter.fetch(id=id, paths=paths)

    @classmethod
    def from_adapter(cls, adapter: SignalAdapter, name: str = "fetch_context", description: Optional[str] = None):
        """
        Dynamically constructs the Tool based on the Adapter.
        v0.2 creates a generic args schema.
        v1.0 will dynamically generate deep pydantic types based on the GraphQL schema itself.
        """
        if description is None:
             description = f"Fetches required context paths for the root '{adapter.root_type}' entity."
             
        # Create a dynamic Pydantic model for the arguments
        DynamicArgsSchema = create_model(
            f"{adapter.root_type}HydrationSchema",
            id=(str, Field(..., description=f"The ID of the {adapter.root_type}")),
            paths=(list[str], Field(..., description="A list of dot-notation paths to fetch, e.g. ['profile.name', 'orders[0].id']"))
        )
        
        tool = cls(
            name=name,
            description=description,
            args_schema=DynamicArgsSchema,
        )
        # Store securely to avoid Pydantic trying to validate the arbitrary adapter instance
        object.__setattr__(tool, "_adapter", adapter)
        
        return tool
