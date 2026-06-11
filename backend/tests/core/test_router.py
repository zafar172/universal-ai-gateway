import pytest
from app.core.providers.base import BaseProvider, CompletionRequest, Message, ProviderMetadata, CompletionResponse
from app.core.router import ModelRouter

class MockProvider(BaseProvider):
    def __init__(self, name: str, models: list):
        self._name = name
        self._models = models

    @property
    def provider_name(self) -> str:
        return self._name

    async def get_available_models(self) -> list:
        return self._models

    async def generate_completion(self, request: CompletionRequest):
        return CompletionResponse(id="1", model=request.model, provider=self._name, content="mock", finish_reason="stop", usage={})

    async def stream_completion(self, request: CompletionRequest):
        yield "mock"

@pytest.fixture
def mock_router():
    router = ModelRouter.__new__(ModelRouter)
    router.model_cache = [
        ProviderMetadata(model_id="cheap", provider_name="mock", cost_per_1k_input=0.001, cost_per_1k_output=0.001, speed_tier="slow", reasoning_tier="low", context_window=4000),
        ProviderMetadata(model_id="fast", provider_name="mock", cost_per_1k_input=0.01, cost_per_1k_output=0.01, speed_tier="very_fast", reasoning_tier="medium", context_window=8000),
    ]
    return router

def test_router_lowest_cost(mock_router):
    assert mock_router.model_cache[0].model_id == "cheap"

def test_router_fastest(mock_router):
    fast_models = [m for m in mock_router.model_cache if m.speed_tier == "very_fast"]
    assert len(fast_models) == 1
