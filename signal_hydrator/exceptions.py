from typing import Any, Dict, List, Optional

class SignalHydratorError(Exception):
    """Base exception for all signal-hydrator errors."""
    pass

class SchemaError(SignalHydratorError):
    """Raised when an adapter's backend schema is invalid or cannot be parsed."""
    pass

class AdapterFetchError(SignalHydratorError):
    """Raised when a SignalAdapter fails to execute a network or database request."""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error

class GraphQLError(AdapterFetchError):
    """Raised when a GraphQL server returns a 200 OK but includes an 'errors' array."""
    def __init__(self, message: str, errors: List[Dict[str, Any]]):
        super().__init__(message)
        self.errors = errors
