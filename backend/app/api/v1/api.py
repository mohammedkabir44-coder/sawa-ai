"""Aggregate all v1 API routers with crash isolation."""
from fastapi import APIRouter

api_router = APIRouter()
CRASH_LOG = {}

def _try_include(module_name):
    try:
        mod = __import__("app.api.v1.endpoints." + module_name, fromlist=["router"])
        api_router.include_router(mod.router)
    except Exception as e:
        import traceback
        CRASH_LOG[module_name] = {"error": str(e), "trace": traceback.format_exc()}

for _m in ["auth", "businesses", "customers", "leads", "products", "services",
           "analytics", "whatsapp_commerce", "whatsapp", "sms", "campaigns",
           "automations", "agents_api"]:
    _try_include(_m)

@api_router.get("/debug-crashes")
def debug_crashes():
    out = []
    for mod, info in CRASH_LOG.items():
        out.append("MODULE: " + mod)
        out.append("ERROR: " + info["error"])
        out.append("TRACEBACK:")
        out.append(info["trace"])
    return "\n".join(out) if out else "NO CRASHES! MODULES LOADED PERFECTLY."
