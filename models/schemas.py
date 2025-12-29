"""
Q-NEXUS — API Schemas
Clear, strict, production-grade
"""

from pydantic import BaseModel, Field
from typing import List, Dict

class MarketPayload(BaseModel):
    prices: List[float] = Field(..., min_items=10)
    volumes: List[float] = Field(..., min_items=10)

class DecisionResponse(BaseModel):
    decision: str = Field(..., example="BUY")
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk: str = Field(..., example="LOW")
    explain: Dict[str, float]
    timestamp: int

class DashboardResponse(BaseModel):
    user: dict
    usage: int
    plan: str
    capabilities: dict
from pydantic import BaseModel, EmailStr

class RegisterPayload(BaseModel):
    email: EmailStr
    plan: str = "starter"

class RegisterResponse(BaseModel):
    api_key: str
    plan: str
    message: str
