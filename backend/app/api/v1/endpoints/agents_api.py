
from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["Sodangi Agents"])

@router.get("/ping")
def ping_test():
    return {"status": "ALIVE", "message": "agents_api.py is fully neutralized. The ghost was in the database imports!"}

@router.get("/health")
def health_test():
    return {"status": "ok", "database": "bypassed"}
