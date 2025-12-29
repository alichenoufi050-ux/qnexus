from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import time
from core.engine import DecisionEngine
from models.schemas import MarketPayload, DecisionResponse, DashboardResponse
from db.memory import get_user_by_key, increment_usage, usage_exceeded

app = FastAPI(
    title="Q-NEXUS OMEGA",
    version="1.0",
    description="Decision Intelligence Platform for Global Markets"
)

ENGINE = DecisionEngine()
class LearnPayload(BaseModel):
    strategy: str
    realized_return: float
def authorize(api_key: str):
    if not api_key:
        raise HTTPException(401, "Missing API Key")

    user = get_user_by_key(api_key)
    if not user:
        raise HTTPException(401, "Invalid API Key")

    increment_usage(api_key)

    if usage_exceeded(api_key):
        raise HTTPException(429, "Usage limit reached")

    return user

@app.get("/")
def root():
    return {
        "name": "Q-NEXUS OMEGA",
        "status": "running"
    }

@app.post("/api/decide", response_model=DecisionResponse)
def decide(payload: MarketPayload, authorization: str = Header(None)):
    authorize(authorization)
    return ENGINE.decide(payload.prices, payload.volumes)
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
@app.get("/api/dashboard", response_model=DashboardResponse)
def dashboard(authorization: str = Header(None)):
    user = authorize(authorization)
    return {
        "user": user,
        "usage": "tracked",
        "plan": user["plan"],
        "capabilities": {
            "markets": ["crypto", "gold", "energy", "stocks"],
            "ai_mode": user["plan"],
        }
    }

@app.get("/health")
def health():
    return {"status": "ok"}
