import pytest
from signal_siphon.adapters.sql import SQLAdapter

def test_sql_adapter_builds_select_queries():
    """
    Test that the experimental SQL adapter can turn dot-notation paths
    into basic SELECT statements with JOINs.
    """
    adapter = SQLAdapter(connection_string="sqlite:///:memory:", root_table="users")
    
    paths = ["profile.name", "orders[0].id", "org.tier"]
    
    query = adapter._build_query(id="123", paths=paths)
    
    # Verify the generated SQL statement (naive parsing for v0.1 tests)
    assert "SELECT" in query
    assert "FROM users" in query
    
    # Should join the inferred tables based on paths
    assert "JOIN profile" in query
    assert "JOIN orders" in query
    assert "JOIN org" in query
    
    # Should select the specific fields
    assert "profile.name" in query
    assert "orders.id" in query
    assert "org.tier" in query
    
    # Should restrict to root ID
    assert "users.id = '123'" in query
