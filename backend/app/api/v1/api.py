"""Aggregate all v1 API routers with crash isolation."""
from fastapi import APIRouter

api_router = APIRouter()

def _try_include(module_name):
    try:
        mod = __import__("app.api.v1.endpoints." + module_name, fromlist=["router"])
        api_router.include_router(mod.router)
        print("LOADED ROUTER: " + module_name)
    except Exception as e:
        print("SKIPPED BROKEN ROUTER: " + module_name + " -> " + repr(e)[:200])

for _m in ["auth", "businesses", "customers", "leads", "products", "services",
           "analytics", "whatsapp_commerce", "whatsapp", "sms", "campaigns",
           "automations", "agents_api"]:
    _try_include(_m)
