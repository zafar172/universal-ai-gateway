import httpx

def log(msg, status="INFO"):
    colors = {"INFO": "\033[94m", "SUCCESS": "\033[92m", "ERROR": "\033[91m", "QWEN": "\033[95m"}
    print(f"{colors.get(status, '')}[QWEN PHASE 2] {msg}\033[0m")

def main():
    log("Starting Phase 2 Memory Validation (Port 8001)...", "QWEN")
    
    # 1. Get Token
    r = httpx.post("http://127.0.0.1:8001/login", json={"email": "validation@test.local", "password": "SuperSecret123"})
    token = r.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create Conversation
    log("Creating new conversation...", "INFO")
    r = httpx.post("http://127.0.0.1:8001/v1/conversations", headers=headers)
    conv_id = r.json().get("conversation_id")
    log(f"Created conversation: {conv_id}", "SUCCESS")
    
    # 3. Send First Message
    log("Sending first message: 'What is the capital of France?'", "INFO")
    r = httpx.post(f"http://127.0.0.1:8001/v1/conversations/{conv_id}/chat", 
                   headers=headers, 
                   json={"messages": [{"role": "user", "content": "What is the capital of France?"}], "routing_strategy": "lowest_cost"})
    ai_response_1 = r.json().get("content", "")
    log(f"AI replied: '{ai_response_1}'", "SUCCESS")
    
    # 4. Send Second Message (Testing memory)
    log("Sending second message: 'And what is its population?'", "INFO")
    r = httpx.post(f"http://127.0.0.1:8001/v1/conversations/{conv_id}/chat", 
                   headers=headers, 
                   json={"messages": [{"role": "user", "content": "And what is its population?"}], "routing_strategy": "lowest_cost"})
    ai_response_2 = r.json().get("content", "")
    log(f"AI replied: '{ai_response_2}'", "SUCCESS")
    
    # 5. Retrieve History
    log("Retrieving full conversation history from database...", "INFO")
    r = httpx.get(f"http://127.0.0.1:8001/v1/conversations/{conv_id}", headers=headers)
    history = r.json().get("messages", [])
    
    if len(history) >= 4:
        log("MEMORY VALIDATION SUCCESSFUL! All messages saved and retrieved.", "SUCCESS")
        print("\n--- SAVED HISTORY ---")
        for msg in history:
            print(f"[{msg['role'].upper()}] {msg['content']}")
        print("---------------------\n")
    else:
        log(f"MEMORY FAILED: Expected 4 messages, got {len(history)}", "ERROR")

if __name__ == "__main__":
    main()
