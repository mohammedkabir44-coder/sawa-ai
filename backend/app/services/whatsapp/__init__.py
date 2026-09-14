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


def get_provider_for_account(account: "WhatsAppAccount") -> WhatsAppProvider:
    """Return a provider configured with a specific tenant's credentials.

    The ``api_key`` on the account is transparently decrypted by the
    EncryptedString type-decorator when the ORM row is loaded, so both
    values passed to Meta are the account's real, stored credentials.

    Falls back to the mock provider (with a loud log) when Meta is selected
    but the account is missing either the token or the phone-number ID — a
    silent mock in production would accept messages without delivering them.
    """
    if settings.WHATSAPP_PROVIDER.lower() == "meta":
        api_key = (account.api_key or "").strip() if account else ""
        phone_number_id = (account.phone_number_id or "").strip() if account else ""
        if api_key and phone_number_id:
            from app.services.whatsapp.meta import MetaWhatsAppProvider

            return MetaWhatsAppProvider(
                access_token=api_key, phone_number_id=phone_number_id
            )
        logger.critical(
            "WHATSAPP_PROVIDER=meta but account %r is missing api_key or "
            "phone_number_id; falling back to MockWhatsAppProvider — messages "
            "for this account will NOT be delivered.",
            getattr(account, "id", None),
        )
    return MockWhatsAppProvider()


__all__ = ["WhatsAppProvider", "get_whatsapp_provider", "get_provider_for_account"]