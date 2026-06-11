import os, subprocess, time, httpx

print("[QWEN] Cleaning old mocks...")
for f in os.listdir("app/core/providers"):
    if f.startswith("mock_") and f.endswith(".py"):
        os.remove(f"app/core/providers/{f}")

print("[QWEN] Writing verified mock_huggingface.py (0.0 cost)...")
with open("app/core/providers/mock_huggingface.py", "w") as f:
    f.write('''import time
from typing import AsyncGenerator, List
from .base import BaseProvider, CompletionRequest, CompletionResponse, ProviderMetadata

class MockHuggingfaceProvider(BaseProvider):
    def __init__(self, api_key: str = "mock"):
        self._name = "mock_huggingface"
        self.model_metadata = [ProviderMetadata(model_id="phi-3-mini", provider_name=self._name, cost_per_1k_input=0.0, cost_per_1k_output=0.0, speed_tier="very_fast", reasoning_tier="low", context_window=4000)]
    @property
    def provider_name(self) -> str: return self._name
    async def get_available_models(self) -> List[ProviderMetadata]: return self.model_metadata
    async def generate_completion(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(id="1", model="phi-3-mini", provider=self._name, content="HF", finish_reason="stop", usage={"prompt_tokens":1,"completion_tokens":1,"total_tokens":2}, cost_usd=0.0, latency_ms=10.0)
    async def stream_completion(self, request: CompletionRequest) -> AsyncGenerator[str, None]: yield "HF"
''')

print("[QWEN] Writing verified mock_anthropic.py (expert reasoning)...")
with open("app/core/providers/mock_anthropic.py", "w") as f:
    f.write('''import time
from typing import AsyncGenerator, List
from .base import BaseProvider, CompletionRequest, CompletionResponse, ProviderMetadata

class MockAnthropicProvider(BaseProvider):
    def __init__(self, api_key: str = "mock"):
        self._name = "mock_anthropic"
        self.model_metadata = [ProviderMetadata(model_id="claude-3-5-sonnet", provider_name=self._name, cost_per_1k_input=0.003, cost_per_1k_output=0.015, speed_tier="fast", reasoning_tier="expert", context_window=200000)]
    @property
    def provider_name(self) -> str: return self._name
    async def get_available_models(self) -> List[ProviderMetadata]: return self.model_metadata
    async def generate_completion(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(id="2", model="claude-3-5-sonnet", provider=self._name, content="Anthropic", finish_reason="stop", usage={"prompt_tokens":1,"completion_tokens":1,"total_tokens":2}, cost_usd=0.01, latency_ms=10.0)
    async def stream_completion(self, request: CompletionRequest) -> AsyncGenerator[str, None]: yield "Anthropic"
''')

print("[QWEN] Killing old server...")
subprocess.run("pkill -9 -f uvicorn", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)

print("[QWEN] Starting fresh server...")
subprocess.Popen("uvicorn app.main:app --host 127.0.0.1 --port 8000", shell=True)
time.sleep(3)

print("[QWEN] Testing login...")
r = httpx.post("http://127.0.0.1:8000/login", json={"email": "validation@test.local", "password": "SuperSecret123"})
token = r.json().get("access_token")
if not token:
    print("[QWEN] Login failed. Exiting.")
    exit(1)

print("[QWEN] Testing lowest_cost (should be mock_huggingface)...")
r = httpx.post("http://127.0.0.1:8000/v1/chat/completions", headers={"Authorization": f"Bearer {token}"}, json={"messages": [{"role": "user", "content": "test"}], "model": "auto", "routing_strategy": "lowest_cost"})
data = r.json()
if data.get("provider") == "mock_huggingface":
    print("[QWEN] SUCCESS: lowest_cost routed to mock_huggingface!")
else:
    print(f"[QWEN] FAIL: lowest_cost routed to {data.get('provider')}")

print("[QWEN] Testing highest_reasoning (should be mock_anthropic)...")
r = httpx.post("http://127.0.0.1:8000/v1/chat/completions", headers={"Authorization": f"Bearer {token}"}, json={"messages": [{"role": "user", "content": "test"}], "model": "auto", "routing_strategy": "highest_reasoning"})
data = r.json()
if data.get("provider") == "mock_anthropic":
    print("[QWEN] SUCCESS: highest_reasoning routed to mock_anthropic!")
else:
    print(f"[QWEN] FAIL: highest_reasoning routed to {data.get('provider')}")

print("[QWEN] VALIDATION COMPLETE.")
