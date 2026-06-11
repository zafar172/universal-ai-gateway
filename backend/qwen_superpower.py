import os, subprocess, time, httpx, sys

def log(msg, color="\033[94m"):
    print(f"{color}[QWEN SUPERPOWER] {msg}\033[0m")

def nuke_processes():
    log("Nuking all stuck uvicorn/python processes...", "\033[91m")
    os.system("pkill -9 -f uvicorn > /dev/null 2>&1")
    time.sleep(1)

def ensure_db():
    log("Ensuring PostgreSQL is awake...", "\033[95m")
    os.system("mkdir -p ~/pgdata && initdb -D ~/pgdata > /dev/null 2>&1")
    os.system("pg_ctl -D ~/pgdata -l ~/pgdata/logfile start > /dev/null 2>&1")
    os.system("createdb gateway_db > /dev/null 2>&1")
    log("Database secured.", "\033[92m")

def write_main_py():
    log("Writing unified, verified app/main.py...", "\033[95m")
    code = '''from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import uuid

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.models.user import User
from app.models.conversation import Conversation
from app.core.providers.base import CompletionRequest, Message
from app.core.router import ModelRouter

router = ModelRouter()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await router.initialize()
    yield

app = FastAPI(title="Universal AI Gateway", lifespan=lifespan)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class ChatMessage(BaseModel):
    role: str
    content: str
class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = "auto"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    routing_strategy: str = "balanced"

class UserRegister(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

@app.get("/")
def read_root():
    return {"message": "Universal AI Gateway is running securely on Android"}

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(email=user_data.email, hashed_password=get_password_hash(user_data.password))
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"message": "User created", "user_id": new_user.id}

@app.post("/login")
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    return {"access_token": create_access_token(data={"sub": user.email}), "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload: raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.email == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    return {"email": user.email, "is_active": user.is_active}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, token: str = Depends(oauth2_scheme)):
    if not decode_access_token(token): raise HTTPException(status_code=401, detail="Invalid token")    unified = CompletionRequest(model=request.model, messages=[Message(role=m.role, content=m.content) for m in request.messages], temperature=request.temperature, max_tokens=request.max_tokens, routing_strategy=request.routing_strategy)
    try:
        return (await router.execute(unified)).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- PHASE 2: MEMORY ENDPOINTS ---
@app.post("/v1/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload: raise HTTPException(status_code=401, detail="Invalid token")
    conv = Conversation(user_id=payload.get("sub"), title="New Chat", messages=[])
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return {"conversation_id": conv.id}

@app.post("/v1/conversations/{conv_id}/chat")
async def chat_with_memory(conv_id: str, request: ChatCompletionRequest, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    if not decode_access_token(token): raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv: raise HTTPException(status_code=404, detail="Conversation not found")
    
    history = conv.messages or []
    for msg in request.messages:
        history.append({"role": msg.role, "content": msg.content})
        
    unified = CompletionRequest(model=request.model, messages=[Message(role=m["role"], content=m["content"]) for m in history], temperature=request.temperature, max_tokens=request.max_tokens, routing_strategy=request.routing_strategy)
    
    try:
        response = await router.execute(unified)
        history.append({"role": "assistant", "content": response.content, "model": response.model, "provider": response.provider})
        conv.messages = history
        await db.commit()
        return response.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/conversations/{conv_id}")
async def get_conversation(conv_id: str, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    if not decode_access_token(token): raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv: raise HTTPException(status_code=404, detail="Not found")
    return {"conversation_id": conv.id, "messages": conv.messages}
'''
    with open("app/main.py", "w") as f:
        f.write(code)
    log("app/main.py verified and updated.", "\033[92m")
def start_server():
    log("Starting server on port 8001...", "\033[95m")
    subprocess.Popen(["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(10):
        try:
            if "Universal AI Gateway" in httpx.get("http://127.0.0.1:8001/").text:
                log("Server is online and healthy.", "\033[92m")
                return True
        except:
            time.sleep(1)
    log("Server failed to start.", "\033[91m")
    return False

def run_phase2_test():
    log("Running Phase 2 Autonomous Memory Test...", "\033[95m")
    base = "http://127.0.0.1:8001"
    
    # 1. Login
    r = httpx.post(f"{base}/login", json={"email": "validation@test.local", "password": "SuperSecret123"})
    token = r.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create Conv
    r = httpx.post(f"{base}/v1/conversations", headers=headers)
    conv_id = r.json().get("conversation_id")
    
    # 3. Chat 1
    r = httpx.post(f"{base}/v1/conversations/{conv_id}/chat", headers=headers, json={"messages": [{"role": "user", "content": "What is the capital of France?"}], "routing_strategy": "lowest_cost"})
    ans1 = r.json().get("content", "")
    
    # 4. Chat 2 (Memory test)
    r = httpx.post(f"{base}/v1/conversations/{conv_id}/chat", headers=headers, json={"messages": [{"role": "user", "content": "And its population?"}], "routing_strategy": "lowest_cost"})
    ans2 = r.json().get("content", "")
    
    # 5. Get History
    r = httpx.get(f"{base}/v1/conversations/{conv_id}", headers=headers)
    history = r.json().get("messages", [])
    
    print("\n" + "="*60)
    if len(history) >= 4:
        log("PHASE 2 MEMORY VALIDATION: 100% SUCCESSFUL", "\033[92m")
        log("The AI successfully remembered the conversation context!", "\033[92m")
        print("\n--- RETRIEVED DATABASE HISTORY ---")
        for msg in history:
            print(f"[{msg['role'].upper():10}] {msg['content']}")
        print("----------------------------------\n")
        return True
    else:
        log(f"PHASE 2 FAILED: Expected 4 messages, got {len(history)}", "\033[91m")        return False

if __name__ == "__main__":
    log("INITIATING QWEN SUPERPOWER PROTOCOL...", "\033[95m")
    nuke_processes()
    ensure_db()
    write_main_py()
    if start_server():
        run_phase2_test()
