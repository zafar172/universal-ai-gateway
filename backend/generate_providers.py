engines = [
    ("huggingface", "phi-3-mini", 0.0, 0.0, "very_fast", "low"),
    ("meta", "llama-3-70b", 0.0005, 0.0005, "very_fast", "medium"),
    ("deepseek", "deepseek-coder-v2", 0.00014, 0.00028, "very_fast", "high"),
    ("mistral", "mixtral-8x7b", 0.0006, 0.0006, "fast", "high"),
    ("google", "gemini-1.5-pro", 0.00125, 0.005, "fast", "high"),
    ("qwen", "qwen-2-72b", 0.0008, 0.0008, "fast", "high"),
    ("ibm", "granite-34b", 0.0005, 0.0005, "medium", "medium"),
    ("nvidia", "nemotron-4-340b", 0.0003, 0.0003, "fast", "medium"),
    ("cohere", "command-r-plus", 0.0025, 0.01, "medium", "expert"),
    ("grok", "grok-beta", 0.005, 0.015, "fast", "expert"),
    ("anthropic", "claude-3-5-sonnet", 0.003, 0.015, "fast", "expert"),
    ("openai", "gpt-4o-mini", 0.00015, 0.0006, "very_fast", "medium"),
]
tpl = """from typing import AsyncGenerator, List
from .base import BaseProvider, CompletionRequest, CompletionResponse, ProviderMetadata
class Mock{C}Provider(BaseProvider):
    def __init__(self, api_key: str = "mock"):
        self._name = "mock_{n}"
        self.model_metadata = [ProviderMetadata(model_id="{m}", provider_name=self._name, cost_per_1k_input={ci}, cost_per_1k_output={co}, speed_tier="{s}", reasoning_tier="{r}", context_window=128000)]
    @property
    def provider_name(self) -> str: return self._name
    async def get_available_models(self) -> List[ProviderMetadata]: return self.model_metadata
    async def generate_completion(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(id="1", model=request.model, provider=self._name, content=f"[{C}]: Ready.", finish_reason="stop", usage={"prompt_tokens":10,"completion_tokens":20,"total_tokens":30}, cost_usd=0.0, latency_ms=100.0)
    async def stream_completion(self, request: CompletionRequest) -> AsyncGenerator[str, None]: yield "Mock"
"""
for n, m, ci, co, s, r in engines:
    with open(f"app/core/providers/mock_{n}.py", "w") as f:
        f.write(tpl.format(C=n.capitalize(), n=n, m=m, ci=ci, co=co, s=s, r=r))
print("Generated 12 mock providers successfully.")
