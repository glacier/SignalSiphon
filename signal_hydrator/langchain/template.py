from typing import Any, Dict, List, Optional
try:
    from langchain_core.prompts import PromptTemplate
except ImportError:
    PromptTemplate = object  # Fallback if langchain isn't installed

from ..templating.jinja import JinjaHydrator
from ..adapters.base import SignalAdapter

class HydratedPromptTemplate(PromptTemplate):
    """
    A LangChain PromptTemplate that automatically statically analyzes its Jinja2 template,
    fetches required fields via SignalAdapters, and fully hydrates the context *before*
    passing the rendered string to the LLM.
    """
    
    ext_adapters: Dict[str, SignalAdapter] = {}
    _hydrator: JinjaHydrator = JinjaHydrator()

    def __init__(self, **kwargs):
        if "template_format" not in kwargs or kwargs["template_format"] != "jinja2":
            raise ValueError("HydratedPromptTemplate currently only supports template_format='jinja2'")
        super().__init__(**kwargs)

    async def aformat(self, **kwargs: Any) -> str:
        """
        Asynchronously format the prompt with the inputs.
        This intercepts the standard rendering process to inject the GraphQL/REST fetches.
        """
        # We need a copy because we are going to mutate it with fetched data
        hydrated_context = {k: v for k, v in kwargs.items()}
        
        # Hydrate all required fields concurrently (or sequentially for v1)
        for root_var, adapter in self.ext_adapters.items():
            if root_var not in hydrated_context:
                continue

            id_val = hydrated_context[root_var].get("id") if isinstance(hydrated_context[root_var], dict) else hydrated_context[root_var]
            if not id_val:
                continue

            # 1. Statically analyze the Jinja template string to find all requested fields
            paths = self._hydrator.extract_paths(self.template, root_var)
            if not paths:
                continue

            # 2. Fetch the data dynamically via the Adapter
            fetched_data = await adapter.fetch(id=str(id_val), paths=paths)

            # 3. Update the context payload
            if isinstance(hydrated_context[root_var], dict):
                hydrated_context[root_var].update(fetched_data)
            else:
                hydrated_context[root_var] = fetched_data

        # 4. Render the template using standard Jinja instead of Langchain's restricted sandbox
        # LangChain blocks `{{ user.profile }}` by default, so we bypass their formatter entirely.
        import jinja2
        env = jinja2.Environment()
        rendered = env.from_string(self.template).render(**hydrated_context)
        
        return rendered

    def format(self, **kwargs: Any) -> str:
        """
        Synchronous formatting is heavily discouraged because it requires blocking
        the thread to execute async network calls. Currently throws an error guiding
        to `aformat()` or `.ainvoke()`.
        """
        raise NotImplementedError(
            "HydratedPromptTemplate performs network requests and must be called asynchronously. "
            "Please use `.aformat(...)` or LangChain's `.ainvoke(...)` instead."
        )
