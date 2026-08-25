"""Aggregate all v1 API routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics,
    auth,
    automations,
    businesses,
    campaigns,
    customers,
    leads,
    products,
    services,
    sms,
    whatsapp_commerce,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(businesses.router)
api_router.include_router(customers.router)
api_router.include_router(leads.router)
api_router.include_router(products.router)
api_router.include_router(services.router)
api_router.include_router(analytics.router)
api_router.include_router(whatsapp_commerce.router)
api_router.include_router(sms.router)
api_router.include_router(campaigns.router)
api_router.include_router(automations.router)
