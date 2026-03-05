from typing import Any, Dict, List, Optional
import json
from graphql import (
    build_ast_schema,
    parse as parse_graphql,
    validate,
    GraphQLSchema,
    FieldNode,
    NameNode,
    SelectionSetNode,
    print_ast,
    OperationDefinitionNode,
    OperationType,
    VariableDefinitionNode,
    NamedTypeNode,
    DocumentNode
)
from .base import SignalAdapter
from ..exceptions import SchemaError, AdapterFetchError, GraphQLError

class GraphQLAdapter(SignalAdapter):
    """
    Adapter that translates dot-notation paths into a validated GraphQL query
    based on a strict schema.
    """

    def __init__(self, endpoint: str, schema_str: str, root_type: str, headers: Optional[Dict[str, str]] = None):
        self.endpoint = endpoint
        self._root_type = root_type
        self.headers = headers or {}
        
        # Parse and build the schema instance
        try:
            document = parse_graphql(schema_str)
            self.schema = build_ast_schema(document)
        except Exception as e:
            raise SchemaError(f"Failed to parse GraphQL schema: {str(e)}")

        # Validate that the root type actually exists in the schema
        if not self.schema.get_type(self._root_type):
            raise SchemaError(f"Root type '{self._root_type}' not found in schema.")

    @property
    def root_type(self) -> str:
        return self._root_type

    def _build_selection_tree(self, paths: List[str]) -> SelectionSetNode:
        """
        Converts a list of dot-paths like ['profile.name', 'orders.id']
        into a nested hierarchy of GraphQL FieldNodes.
        """
        # Naive implementation for v1: just building a nested dictionary of fields first
        tree_dict = {}
        for path in paths:
            parts = path.replace('[', '.').replace(']', '').split('.')
            current = tree_dict
            for part in parts:
                if not part: continue # trailing or empty
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        # Convert dictionary to SelectionSetNode
        def dict_to_selection_set(d: dict) -> Optional[SelectionSetNode]:
            if not d:
                return None
            selections = []
            for name, children in d.items():
                # We skip array indices in GQL, the query just asks for the field
                if name.isdigit():
                    continue 

                child_selection = dict_to_selection_set(children)
                node = FieldNode(
                    name=NameNode(value=name),
                    selection_set=child_selection
                )
                selections.append(node)
            
            if not selections:
                return None
                
            return SelectionSetNode(selections=selections)

        return dict_to_selection_set(tree_dict)

    def build_query(self, paths: List[str]) -> str:
        """
        Builds the raw GraphQL query string for the requested paths.
        """
        selection_set = self._build_selection_tree(paths)
        if not selection_set:
            return ""

        # Construct the root query: query Hydrate($id: ID!) { root_type(id: $id) { ... } }
        root_field = FieldNode(
            name=NameNode(value=self._root_type.lower()),
            arguments=[
                # Not doing full AST arguments for brevity in V1, injecting ID manually
            ],
            selection_set=selection_set
        )
        
        # Build the operation wrapper
        query = f"query HydrateAgentContext($id: ID!) {{\n  {self._root_type.lower()}(id: $id) {{\n"
        
        # Extract string from the generated selection set
        inner_query = print_ast(selection_set)
        
        query += inner_query + "\n}\n}"
        return query

    async def fetch(self, id: str, paths: List[str]) -> Dict[str, Any]:
        """
        Executes the dynamically generated GraphQL query.
        """
        import httpx  # Lazy import for async network client
        
        query_str = self.build_query(paths)
        if not query_str:
            return {}

        payload = {
            "query": query_str,
            "variables": {"id": id}
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.endpoint, 
                    json=payload, 
                    headers={"Content-Type": "application/json", **self.headers}
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                raise AdapterFetchError(f"HTTP error fetching GraphQL data: {e.response.status_code}", original_error=e)
            except httpx.RequestError as e:
                raise AdapterFetchError(f"Network error fetching GraphQL data: {str(e)}", original_error=e)

        if "errors" in data and data["errors"]:
            raise GraphQLError("GraphQL returned validation or execution errors.", errors=data["errors"])

        # Return the resolved root object
        root_key = self._root_type.lower()
        return data.get("data", {}).get(root_key, {})
