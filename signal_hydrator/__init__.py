from .adapters.base import SignalAdapter
from .adapters.graphql import GraphQLAdapter
from .adapters.rest import RESTAdapter
from .adapters.sql import SQLAdapter

from .templating.jinja import JinjaHydrator

from .runtime.proxy import ContextProxy
from .runtime.dataloader import AsyncDataLoader

from .exceptions import SignalHydratorError, SchemaError, AdapterFetchError, GraphQLError

__version__ = "0.1.0"
# Export specific components if the user has LangChain installed
try:
    from .langchain.template import HydratedPromptTemplate
    from .langchain.tool import HydratorTool
    __all__ = [
        "SignalAdapter", "GraphQLAdapter", "RESTAdapter", "SQLAdapter",
        "JinjaHydrator", "ContextProxy", "AsyncDataLoader",
        "HydratedPromptTemplate", "HydratorTool"
    ]
except ImportError:
    __all__ = [
        "SignalAdapter", "GraphQLAdapter", "RESTAdapter", "SQLAdapter",
        "JinjaHydrator", "ContextProxy", "AsyncDataLoader"
    ]
