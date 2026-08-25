"""WhatsApp provider factory."""
import logging

from app.core.config import settings
from app.services.whatsapp.base import WhatsAppProvider
from app.services.whatsapp.mock import MockWhatsAppProvider

logger = logging.getLogger(__name__)


def get_whatsapp_provider() -> WhatsAppProvider:
    """Return the configured WhatsApp provider.

    Controlled by the ``WHATSAPP_PROVIDER`` environment variable.
    Real providers are only used when credentials are present.

    In production, falling through to MockWhatsAppProvider is a silent
    failure mode — messages (including payment confirmations) are
    accepted but never actually delivered. We keep the same default
    behavior (never hard-fail app startup over this) but log loudly so
    it's visible in production logs/alerts instead of failing silently.
    """
    provider = settings.WHATSAPP_PROVIDER.lower()
    is_production = getattr(settings, "ENVIRONMENT", "development").lower() == "production"

    if provider == "meta" and settings.WHATSAPP_ACCESS_TOKEN:
        from app.services.whatsapp.meta import MetaWhatsAppProvider

        return MetaWhatsAppProvider(
            access_token=settings.WHATSAPP_ACCESS_TOKEN,
            phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID,
        )

    if is_production:
        if provider == "meta":
            logger.critical(
                "WHATSAPP_PROVIDER=meta but WHATSAPP_ACCESS_TOKEN is not "
                "set; falling back to MockWhatsAppProvider — outbound "
                "WhatsApp messages will NOT be delivered."
            )
        else:
            logger.critical(
                "WHATSAPP_PROVIDER=%r in production (expected 'meta'); "
                "falling back to MockWhatsAppProvider — outbound "
                "WhatsApp messages will NOT be delivered.",
                provider,
            )

    # Default to the clearly-labelled mock provider for development.
    return MockWhatsAppProvider()


__all__ = ["WhatsAppProvider", "get_whatsapp_provider"]