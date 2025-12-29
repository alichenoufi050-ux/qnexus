from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import time

from core.engine import DecisionEngine
from models.schemas import (
    MarketPayload,
    DecisionResponse,
    DashboardResponse,
    RegisterPayload,
    RegisterResponse
)
from db.memory import (
    get_user_by_key,
    increment_usage,
    usage_exceeded,
    create_user
)

# =========================
# APP
# =========================
app = FastAPI(
    title="Q-NEXUS OMEGA",
    version="1.0",
    description="Decision Intelligence Platform for Global Markets"
)

ENGINE = DecisionEngine()

# =========================
# AUTH
# =========================
def authorize(api_key: str):
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")

    user = get_user_by_key(api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    increment_usage(api_key)

    if usage_exceeded(api_key):
        raise HTTPException(status_code=429, detail="Usage limit reached")

    return user

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {
        "name": "Q-NEXUS OMEGA",
        "status": "running"
    }

# =========================
# REGISTER  ✅ (سيظهر في /docs)
# =========================
@app.post("/api/register", response_model=RegisterResponse)
def register(payload: RegisterPayload):
    api_key = create_user(
        email=payload.email,
        plan=payload.plan
    )
    return {
        "api_key": api_key,
        "plan": payload.plan,
        "message": "User registered successfully"
    }

# =========================
# DECIDE
# =========================
@app.post("/api/decide", response_model=DecisionResponse)
def decide(payload: MarketPayload, authorization: str = Header(None)):
    authorize(authorization)
    return ENGINE.decide(payload.prices, payload.volumes)

# =========================
# LEARN
# =========================
class LearnPayload(BaseModel):
    strategy: str
    realized_return: float

@app.post("/api/learn")
def learn(payload: LearnPayload, authorization: str = Header(None)):
    authorize(authorization)

    ENGINE.learn(
        executed_strategy=payload.strategy,
        realized_return=payload.realized_return
    )

    return {
        "status": "learning_update_applied",
        "strategy": payload.strategy,
        "return": payload.realized_return,
        "timestamp": int(time.time())
    }

# =========================
# DASHBOARD
# =========================
@app.get("/api/dashboard", response_model=DashboardResponse)
def dashboard(authorization: str = Header(None)):
    user = authorize(authorization)
    return {
        "user": user,
        "usage": "tracked",
        "plan": user["plan"],
        "capabilities": {
            "markets": ["crypto", "gold", "energy", "stocks"],
            "ai_mode": user["plan"]
        }
    }

# =========================
# HEALTH
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}
