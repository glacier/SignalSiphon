from typing import Any, Dict, List
import asyncio
from .base import SignalAdapter

class SQLAdapter(SignalAdapter):
    """
    An experimental adapter that translates dot-notation paths
    into literal SQL SELECT queries with LEFT JOINs.
    Requires SQLAlchemy.
    """

    def __init__(self, connection_string: str, root_table: str):
        self.connection_string = connection_string
        self._root_table = root_table
        
    @property
    def root_type(self) -> str:
        return self._root_table.capitalize()

    def _build_query(self, id: str, paths: List[str]) -> str:
        """
        Dynamically constructs a raw SQL query.
        Example paths: ["profile.name", "orders.id", "settings.theme"]
        """
        # 1. Extract the required tables (joins)
        tables_to_join = set()
        fields_to_select = set()
        
        for path in paths:
             # Remove list indexing like [0] for SQL translation
             import re
             clean_path = re.sub(r'\[\d+\]', '', path)
             parts = clean_path.split('.')
             
             if len(parts) == 1:
                 # Direct property on the root table (e.g. "email")
                 fields_to_select.add(f"{self._root_table}.{parts[0]}")
             else:
                 # It's a relationship. The first part is the table.
                 table_name = parts[0]
                 tables_to_join.add(table_name)
                 fields_to_select.add(f"{table_name}.{parts[1]}")

        # 2. Build the SELECT clause
        select_clause = "SELECT " + ", ".join(list(fields_to_select))
        
        # 3. Build the FROM clause
        from_clause = f"FROM {self._root_table}"
        
        # 4. Build the JOIN clauses (Naive assumption for experimental V1: FK is `{root_table}_id`)
        join_clauses = ""
        for table in tables_to_join:
            join_clauses += f" LEFT JOIN {table} ON {table}.{self._root_table}_id = {self._root_table}.id"
            
        # 5. Build the WHERE clause
        where_clause = f"WHERE {self._root_table}.id = '{id}'"
        
        return f"{select_clause} {from_clause}{join_clauses} {where_clause};"

    async def fetch(self, id: str, paths: List[str]) -> Dict[str, Any]:
        """
        Executes the built SQL query.
        For V1, this is a mock implementation acknowledging the experimental nature.
        """
        query = self._build_query(id, paths)
        
        # In a real implementation, you would use asyncpg/aiosqlite here.
        # This just returns the mocked test data to prove the adapter structure.
        return {"mock_sql": query}
