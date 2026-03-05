from typing import List, Set, Dict, Any
from jinja2 import Environment
from jinja2 import nodes

class JinjaHydrator:
    """
    Parses Jinja2 templates via AST to extract all requested dot-paths
    for a given context variable before the template is rendered.
    """

    def __init__(self):
        # We explicitly cast `None` to the string "None" instead of the default empty string
        # so that LLM prompts clearly show missing data context.
        self.env = Environment(finalize=lambda x: "None" if x is None else x)

    def extract_paths(self, template_str: str, root_var: str) -> List[str]:
        """
        Parses the template string and returns a list of all accessed
        paths for the given root variable.
        
        Example: "User {{ user.profile.name }} in {{ user.org.tier }}"
        Returns: ["profile.name", "org.tier"]
        """
        ast = self.env.parse(template_str)
        paths: Set[str] = set()

        def _walk(node: nodes.Node):
            if isinstance(node, nodes.Getattr):
                # When we hit a Getattr (e.g., user.profile.name)
                # We need to backtrack from the leaf up to the root Name node
                path_parts = []
                current = node
                while isinstance(current, (nodes.Getattr, nodes.Getitem)):
                    if isinstance(current, nodes.Getattr):
                        path_parts.insert(0, current.attr)
                    elif isinstance(current, nodes.Getitem):
                         # If it's a dict/list access like items[0], we append [0]
                         if isinstance(current.arg, nodes.Const):
                            path_parts.insert(0, f"[{current.arg.value}]")
                    current = current.node

                # Once we hit the base, check if it's our target root_var
                if isinstance(current, nodes.Name) and current.name == root_var:
                    # Construct the dot path
                    full_path = ""
                    for part in path_parts:
                        if part.startswith("["):
                            full_path += part
                        else:
                            if full_path:
                                full_path += "."
                            full_path += part
                    if full_path:
                        paths.add(full_path)

            # Recurse down all children
            for child_node in node.iter_child_nodes():
                _walk(child_node)

        _walk(ast)
        
        # Filter out intermediate paths. If we have "profile" and "profile.name",
        # keep only "profile.name"
        final_paths = []
        path_list = list(paths)
        for p in path_list:
            # Check if this path is a prefix of any OTHER path
            is_prefix = any(other.startswith(p + ".") or other.startswith(p + "[") for other in path_list if other != p)
            if not is_prefix:
                final_paths.append(p)
                
        return final_paths

    async def hydrate_context(self, template_str: str, adapters: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Helper that extracts paths for all adapters, fetches the data,
        injects it into the context, and renders the template.
        """
        for root_var, adapter in adapters.items():
            if root_var not in context:
                continue

            id_val = context[root_var].get("id") if isinstance(context[root_var], dict) else context[root_var]
            if not id_val:
                continue
                
            paths = self.extract_paths(template_str, root_var)
            if not paths:
                continue
            
            # Fetch using the adapter
            hydrated_data = await adapter.fetch(id=str(id_val), paths=paths)
            
            # Update the context dictionary with the fetched data
            if isinstance(context[root_var], dict):
                context[root_var].update(hydrated_data)
            else:
                context[root_var] = hydrated_data

        template = self.env.from_string(template_str)
        return template.render(**context)
