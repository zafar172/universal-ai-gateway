import importlib
import pkgutil
import logging
from typing import Dict, Type
from .base import BaseProvider

logger = logging.getLogger(__name__)

class ProviderRegistry:
    _instance = None
    _providers: Dict[str, BaseProvider] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProviderRegistry, cls).__new__(cls)
            cls._instance._load_providers()
        return cls._instance

    def _load_providers(self):
        import app.core.providers as providers_pkg
        for _, module_name, _ in pkgutil.iter_modules(providers_pkg.__path__):
            if module_name in ["base", "registry"]:
                continue
            try:
                module = importlib.import_module(f"app.core.providers.{module_name}")
                class_name = "".join(word.capitalize() for word in module_name.split('_')) + "Provider"
                provider_class: Type[BaseProvider] = getattr(module, class_name)
                instance = provider_class(api_key="mock_key")
                self._providers[instance.provider_name] = instance
                logger.info(f"Loaded provider: {instance.provider_name}")
            except Exception as e:
                logger.error(f"Failed to load {module_name}: {e}")

    def get_provider(self, name: str) -> BaseProvider:
        return self._providers[name]

    def get_all_providers(self) -> Dict[str, BaseProvider]:
        return self._providers
