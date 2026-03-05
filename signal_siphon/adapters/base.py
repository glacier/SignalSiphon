from abc import ABC, abstractmethod
from typing import Any, Dict, List

class SignalAdapter(ABC):
    """
    Abstract base class for all signal adapters.
    An adapter is responsible for taking a list of requested dot-notation paths
    and fetching them for a given ID.
    """

    @property
    @abstractmethod
    def root_type(self) -> str:
        """The base entity this adapter handles (e.g., 'User')."""
        pass

    @abstractmethod
    async def fetch(self, id: str, paths: List[str]) -> Dict[str, Any]:
        """
        Takes an ID and a list of required dot-notation paths.
        Returns a nested dictionary of the hydrated data.
        
        Args:
            id: The unique identifier for the root object.
            paths: A list of string dot-paths (e.g., ["profile.name", "orders[0].id"])
            
        Returns:
            Dict: The fully nested context dictionary.
        """
        pass
