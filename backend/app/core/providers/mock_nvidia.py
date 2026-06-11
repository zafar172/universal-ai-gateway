from typing import AsyncGenerator, List
from .base import BaseProvider, CompletionRequest, CompletionResponse, ProviderMetadata
class MockNvidiaProvider(BaseProvider):
    def __init__(self, api_key: str = "mock"):
        self._name = "mock_nvidia"
        self.model_metadata = [ProviderMetadata(model_id="nemotron-4-340b", provider_name=self._name, cost_per_1k_input=0.0003, cost_per_1k_output=0.0003, speed_tier="fast", reasoning_tier="medium", context_window=128000)]
    @property
    def provider_name(self) -> str: return self._name
    async def get_available_models(self) -> List[ProviderMetadata]: return self.model_metadata
    async def generate_completion(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(id="1", model=request.model, provider=self._name, content=f"[Nvidia]: Ready.", finish_reason="stop", usage={"prompt_tokens":10,"completion_tokens":20,"total_tokens":30}, cost_usd=0.0, latency_ms=100.0)
    async def stream_completion(self, request: CompletionRequest) -> AsyncGenerator[str, None]: yield "Mock"
