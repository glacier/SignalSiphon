import pytest
from signal_hydrator import JinjaHydrator

def test_extract_simple_paths():
    hydrator = JinjaHydrator()
    template = "Hello {{ user.profile.name }}, your tier is {{ user.org.tier }}"
    
    paths = hydrator.extract_paths(template, "user")
    
    # Order isn't guaranteed with sets, so we check inclusion
    assert len(paths) == 2
    assert "profile.name" in paths
    assert "org.tier" in paths

def test_extract_nested_list_paths():
    hydrator = JinjaHydrator()
    template = "Your first order ID is {{ user.orders[0].id }}"
    
    paths = hydrator.extract_paths(template, "user")
    
    assert len(paths) == 1
    assert "orders[0].id" in paths

def test_extract_loop_paths():
    hydrator = JinjaHydrator()
    template = '''
    {% for ticket in user.tickets %}
        Ticket ID: {{ ticket.id }}
        Status: {{ ticket.status }}
    {% endfor %}
    '''
    
    paths = hydrator.extract_paths(template, "user")
    assert len(paths) == 1
    # Ast parsing on loops often just extracts the base iterable for the root var
    assert "tickets" in paths

def test_ignores_other_vars():
    hydrator = JinjaHydrator()
    template = "Hello {{ user.name }}, this is {{ system.date }}"
    
    paths = hydrator.extract_paths(template, "user")
    assert len(paths) == 1
    assert "name" in paths

@pytest.mark.asyncio
async def test_explicit_none_rendering():
    hydrator = JinjaHydrator()
    template = "Your age is {{ user.profile.age }}."
    
    # Simulate a fetch where `age` is None (null from GraphQL)
    context = {"user": {"profile": {"age": None}}}
    
    # We can use a dummy adapter or just directly render to verify Jinja env
    env_template = hydrator.env.from_string(template)
    rendered = env_template.render(**context)
    
    assert rendered == "Your age is None."
