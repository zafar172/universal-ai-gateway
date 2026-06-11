from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator

class Message(BaseModel):
    role: str
    content: str

class CompletionRequest(BaseModel):
    model: str = "auto"
    messages: List[Message]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    routing_strategy: str = "balanced"

class ProviderMetadata(BaseModel):
    model_id: str
    provider_name: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    speed_tier: str
    reasoning_tier: str
    context_window: int

class CompletionResponse(BaseModel):
    id: str
    model: str
    provider: str
    content: str
    finish_reason: str
    usage: dict
    cost_usd: float
    latency_ms: float

class BaseProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: pass

    @abstractmethod
    async def get_available_models(self) -> List[ProviderMetadata]: pass

    @abstractmethod
    async def generate_completion(self, request: CompletionRequest) -> CompletionResponse: pass

    @abstractmethod
    async def stream_completion(self, request: CompletionRequest) -> AsyncGenerator[str, None]: pass
