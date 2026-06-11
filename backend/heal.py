import os, subprocess, time, httpx

def run(cmd):
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    print("[QWEN] Initiating Self-Healing Protocol...")
    for attempt in range(3):
        try:
            run("pkill -9 -f uvicorn")
            time.sleep(1)
            run("mkdir -p ~/pgdata && initdb -D ~/pgdata >/dev/null 2>&1")
            run("pg_ctl -D ~/pgdata -l ~/pgdata/logfile start >/dev/null 2>&1")
            run("createdb gateway_db >/dev/null 2>&1")
            
            code = "from fastapi import FastAPI, Depends, HTTPException, status\nfrom fastapi.security import OAuth2PasswordBearer\nfrom sqlalchemy.ext.asyncio import AsyncSession\nfrom sqlalchemy import select\nfrom pydantic import BaseModel\nfrom typing import List, Optional\nfrom contextlib import asynccontextmanager\nfrom app.core.database import get_db\nfrom app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token\nfrom app.models.user import User\nfrom app.models.conversation import Conversation\nfrom app.core.providers.base import CompletionRequest, Message\nfrom app.core.router import ModelRouter\n\nrouter = ModelRouter()\n\n@asynccontextmanager\nasync def lifespan(app: FastAPI):\n    await router.initialize()\n    yield\n\napp = FastAPI(title='Universal AI Gateway', lifespan=lifespan)\noauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')\n\nclass ChatMessage(BaseModel):\n    role: str\n    content: str\n\nclass ChatCompletionRequest(BaseModel):\n    messages: List[ChatMessage]\n    model: str = 'auto'\n    routing_strategy: str = 'balanced'\n\nclass UserLogin(BaseModel):\n    email: str\n    password: str\n\n@app.get('/')\ndef read_root(): return {'message': 'Running'}\n\n@app.post('/login')\nasync def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):\n    result = await db.execute(select(User).where(User.email == user_data.email))\n    user = result.scalar_one_or_none()\n    if not user or not verify_password(user_data.password, user.hashed_password):\n        raise HTTPException(status_code=400, detail='Invalid')\n    return {'access_token': create_access_token(data={'sub': user.email}), 'token_type': 'bearer'}\n\n@app.post('/v1/conversations', status_code=status.HTTP_201_CREATED)\nasync def create_conv(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):\n    payload = decode_access_token(token)\n    conv = Conversation(user_id=payload.get('sub'), title='Chat', messages=[])\n    db.add(conv); await db.commit(); await db.refresh(conv)\n    return {'conversation_id': conv.id}\n\n@app.post('/v1/conversations/{conv_id}/chat')\nasync def chat_mem(conv_id: str, request: ChatCompletionRequest, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):\n    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))\n    conv = result.scalar_one_or_none()\n    if not conv: raise HTTPException(status_code=404, detail='Not found')\n    history = conv.messages or []\n    for msg in request.messages: history.append({'role': msg.role, 'content': msg.content})\n    unified = CompletionRequest(model=request.model, messages=[Message(role=m['role'], content=m['content']) for m in history], routing_strategy=request.routing_strategy)\n    response = await router.execute(unified)\n    history.append({'role': 'assistant', 'content': response.content, 'model': response.model, 'provider': response.provider})\n    conv.messages = history\n    await db.commit()\n    return response.model_dump()\n\n@app.get('/v1/conversations/{conv_id}')\nasync def get_conv(conv_id: str, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):\n    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))\n    conv = result.scalar_one_or_none()\n    return {'conversation_id': conv.id, 'messages': conv.messages or []}"

            with open("app/main.py", "w") as f:
                f.write(code.replace("\\n", "\n"))
            
            subprocess.Popen(["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            
            base = "http://127.0.0.1:8001"
            r = httpx.post(f"{base}/login", json={"email": "validation@test.local", "password": "SuperSecret123"})
            token = r.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            r = httpx.post(f"{base}/v1/conversations", headers=headers)
            cid = r.json().get("conversation_id")
            
            r = httpx.post(f"{base}/v1/conversations/{cid}/chat", headers=headers, json={"messages": [{"role": "user", "content": "Capital?"}], "routing_strategy": "lowest_cost"})
            r = httpx.post(f"{base}/v1/conversations/{cid}/chat", headers=headers, json={"messages": [{"role": "user", "content": "Population?"}], "routing_strategy": "lowest_cost"})
            
            r = httpx.get(f"{base}/v1/conversations/{cid}", headers=headers)
            hist = r.json().get("messages", [])
            
            if len(hist) >= 4:
                print("\n[QWEN] PHASE 2 MEMORY VALIDATION: 100% SUCCESSFUL!")
                return True
            else:
                raise Exception(f"Got {len(hist)} msgs")
        except Exception as e:
            print(f"[QWEN] Error: {e}. Self-correcting (Attempt {attempt+1}/3)...")
            time.sleep(2)
            
    print("[QWEN] Failed after 3 attempts.")

if __name__ == "__main__":
    main()