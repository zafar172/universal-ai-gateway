from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
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
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
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

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, token: str = Depends(oauth2_scheme)):
    if not decode_access_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    unified = CompletionRequest(model=request.model, messages=[Message(role=m.role, content=m.content) for m in request.messages], temperature=request.temperature, max_tokens=request.max_tokens, routing_strategy=request.routing_strategy)
    try:
        return (await router.execute(unified)).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload: raise HTTPException(status_code=401, detail="Invalid token")
    email = payload.get("sub")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    new_conv = Conversation(user_id=user.id, title="New Conversation", messages=[])
    db.add(new_conv)
    await db.commit()
    await db.refresh(new_conv)
    return {"conversation_id": new_conv.id}

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
    return {"conversation_id": conv.id, "messages": conv.messages or []}
