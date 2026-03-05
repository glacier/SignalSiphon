from typing import List, Set

class ContextProxy:
    """
    A magic proxy object that records all property accesses (dot-notation paths)
    made against it, without actually executing any network requests.
    """
    
    def __init__(self, id: str, adapter: 'SignalAdapter', path_prefix: str = ""):
        # We use __dict__ assignment to bypass our own __setattr__/__getattr__ overrides
        self.__dict__["_id"] = id
        self.__dict__["_adapter"] = adapter
        self.__dict__["_path_prefix"] = path_prefix
        self.__dict__["_recorded_paths"] = set()
        
    def _record_path(self, path: str):
        full_path = f"{self._path_prefix}.{path}" if self._path_prefix else path
        
        # Walk up the chain of parent proxies (if any) to record at the root
        current = self
        while "_parent" in current.__dict__:
            current = current.__dict__["_parent"]
            
        current.__dict__["_recorded_paths"].add(full_path)

    def _get_pending_paths(self) -> List[str]:
        """Returns all deeply nested paths accessed on this proxy instances and its descendants."""
        return list(self.__dict__["_recorded_paths"])

    def __getattr__(self, name: str) -> "ContextProxy":
        """
        Intercepts dot-notation access (e.g., target.profile)
        Records the path and returns a new nested ContextProxy.
        """
        # Exclude private/magic methods from recording
        if name.startswith("_"):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
            
        self._record_path(name)
        
        # Create a child proxy to handle further nesting (e.g. target.profile.name)
        new_prefix = f"{self._path_prefix}.{name}" if self._path_prefix else name
        child = ContextProxy(id=self._id, adapter=self._adapter, path_prefix=new_prefix)
        child.__dict__["_parent"] = self
        return child

    def __getitem__(self, key) -> "ContextProxy":
        """
        Intercepts dictionary/list style access (e.g., target.orders[0])
        Records the path and returns a new nested ContextProxy.
        """
        path_segment = f"[{key}]"
        self._record_path(path_segment)
        
        new_prefix = f"{self._path_prefix}{path_segment}"
        child = ContextProxy(id=self._id, adapter=self._adapter, path_prefix=new_prefix)
        child.__dict__["_parent"] = self
        return child
