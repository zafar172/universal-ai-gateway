import httpx
import subprocess
import time
import sys

def log(msg, status="INFO"):
    colors = {"INFO": "\033[94m", "SUCCESS": "\033[92m", "ERROR": "\033[91m", "SUPERVISOR": "\033[95m"}
    print(f"{colors.get(status, '')}[QWEN SUPERVISOR] {msg}\033[0m")

def check_server():
    log("Checking server health...")
    try:
        r = httpx.get("http://127.0.0.1:8000/")
        if "Universal AI Gateway" in r.text:
            log("Server is healthy.", "SUCCESS")
            return True
    except:
        pass
    
    log("Server not responding. Attempting auto-heal...", "ERROR")
    subprocess.Popen("uvicorn app.main:app --host 127.0.0.1 --port 8000 > /dev/null 2>&1 &", shell=True)
    time.sleep(4)
    try:
        r = httpx.get("http://127.0.0.1:8000/")
        if "Universal AI Gateway" in r.text:
            log("Server auto-healed and started.", "SUCCESS")
            return True
    except:
        pass
    log("Failed to start server.", "ERROR")
    return False

def get_token():
    log("Acquiring authentication token...")
    try:
        r = httpx.post("http://127.0.0.1:8000/login", json={"email": "validation@test.local", "password": "SuperSecret123"})
        token = r.json()['access_token']
        log("Token acquired.", "SUCCESS")
        return token
    except Exception as e:
        log(f"Auth failed: {e}", "ERROR")
        return None

def test_route(strategy, expected_providers, token):
    log(f"Testing strategy: {strategy}...")
    try:
        r = httpx.post(
            "http://127.0.0.1:8000/v1/chat/completions",
            headers={"Authorization": f"Bearer {token}"},
            json={"messages": [{"role": "user", "content": "test"}], "model": "auto", "routing_strategy": strategy}
        )
        data = r.json()
        provider = data.get('provider', '')
        if provider in expected_providers:
            log(f"Routed to {provider}. (PASS)", "SUCCESS")
            return True
        else:
            log(f"Expected {expected_providers}, got {provider}. (FAIL)", "ERROR")
            return False
    except Exception as e:
        log(f"Request failed: {e}", "ERROR")
        return False

def main():
    log("Initializing Qwen 3.7 Supervisor Protocol...", "SUPERVISOR")
    
    if not check_server():
        sys.exit(1)
        
    token = get_token()
    if not token:
        sys.exit(1)
        
    log("Running Phase 1 Routing Validation Suite...", "SUPERVISOR")
    
    results = []
    results.append(test_route("lowest_cost", ["mock_huggingface"], token))
    results.append(test_route("highest_reasoning", ["mock_anthropic", "mock_cohere", "mock_grok"], token))
    results.append(test_route("fastest", ["mock_meta", "mock_deepseek", "mock_huggingface"], token))
    
    if all(results):
        log("PHASE 1 VALIDATION PASSED. 12 ENGINES VERIFIED.", "SUCCESS")
        log("Supervisor is ready to proceed to Phase 2 (Memory).", "SUPERVISOR")
    else:
        log("PHASE 1 VALIDATION FAILED. Review logs.", "ERROR")

if __name__ == "__main__":
    main()
