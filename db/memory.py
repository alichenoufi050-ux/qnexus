"""
Q-NEXUS — In-Memory Data Layer (MVP)
Upgradeable to PostgreSQL / Redis without breaking API
"""

import uuid
import time
from typing import Dict

# =========================
# STORAGE (MVP)
# =========================
USERS: Dict[str, dict] = {}
API_KEYS: Dict[str, str] = {}
USAGE: Dict[str, int] = {}

PLANS = {
    "starter": {
        "limit": 500,
        "features": ["basic_ai"],
    },
    "pro": {
        "limit": 5000,
        "features": ["advanced_ai", "risk_engine"],
    },
    "enterprise": {
        "limit": 50000,
        "features": ["full_ai", "priority", "custom_models"],
    },
}

# =========================
# USER MANAGEMENT
# =========================
def create_user(email: str, plan: str) -> str:
    if plan not in PLANS:
        raise ValueError("Invalid plan")

    user_id = str(uuid.uuid4())
    api_key = str(uuid.uuid4())

    USERS[user_id] = {
        "id": user_id,
        "email": email,
        "plan": plan,
        "features": PLANS[plan]["features"],
        "created_at": int(time.time()),
        "active": True,
    }

    API_KEYS[api_key] = user_id
    USAGE[api_key] = 0

    return api_key

def get_user_by_key(api_key: str) -> dict:
    user_id = API_KEYS.get(api_key)
    if not user_id:
        return None
    return USERS.get(user_id)

def increment_usage(api_key: str):
    if api_key not in USAGE:
        USAGE[api_key] = 0
    USAGE[api_key] += 1

def usage_exceeded(api_key: str) -> bool:
    user = get_user_by_key(api_key)
    if not user:
        return True
    plan = user["plan"]
    return USAGE[api_key] > PLANS[plan]["limit"]
