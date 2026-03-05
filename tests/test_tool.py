import pytest
from signal_hydrator.langchain.tool import HydratorTool
from signal_hydrator.adapters.base import SignalAdapter
from typing import List, Dict, Any

class MockAdapter(SignalAdapter):
    @property
    def root_type(self) -> str:
        return "User"
        
    async def fetch(self, id: str, paths: List[str]) -> Dict[str, Any]:
        return {"profile": {"name": "Test"}}

def test_hydrator_tool_initialization():
    adapter = MockAdapter()
    tool = HydratorTool.from_adapter(adapter, name="fetch_user", description="Fetches user details")
    
    assert tool.name == "fetch_user"
    assert tool.description == "Fetches user details"
    
    # Verify the generated arguments schema has the required fields
    schema = tool.args_schema.model_json_schema()
    assert "id" in schema["properties"]
    assert "paths" in schema["properties"]
    assert schema["properties"]["paths"]["type"] == "array"
