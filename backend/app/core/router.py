import time
from typing import List
from .providers.base import BaseProvider, CompletionRequest, CompletionResponse, ProviderMetadata
from .providers.registry import ProviderRegistry

class ModelRouter:
    def __init__(self):
        self.registry = ProviderRegistry()
        self.model_cache: List[ProviderMetadata] = []
        self._initialized = False

    async def initialize(self):
        if not self._initialized:
            await self._refresh_cache()
            self._initialized = True

    async def _refresh_cache(self):
        self.model_cache = []
        for provider in self.registry.get_all_providers().values():
            models = await provider.get_available_models()
            self.model_cache.extend(models)

    def route(self, request: CompletionRequest) -> BaseProvider:
        if not self.model_cache:
            raise RuntimeError("Router not initialized or no providers available.")

        candidates = self.model_cache.copy()
        strategy = request.routing_strategy
        
        if strategy == "lowest_cost":
            candidates.sort(key=lambda x: x.cost_per_1k_input + x.cost_per_1k_output)
        elif strategy == "fastest":
            tier_map = {"very_fast": 0, "fast": 1, "medium": 2, "slow": 3}
            candidates.sort(key=lambda x: tier_map.get(x.speed_tier, 3))
        elif strategy == "highest_reasoning":
            tier_map = {"expert": 0, "high": 1, "medium": 2, "low": 3}
            candidates.sort(key=lambda x: tier_map.get(x.reasoning_tier, 3))
        else:
            candidates.sort(key=lambda x: (x.cost_per_1k_input * 10))

        best_model = candidates[0]
        request.model = best_model.model_id
        return self.registry.get_provider(best_model.provider_name)

    async def execute(self, request: CompletionRequest) -> CompletionResponse:
        start_time = time.perf_counter()
        provider = self.route(request)
        response = await provider.generate_completion(request)
        response.latency_ms = (time.perf_counter() - start_time) * 1000
        return response
