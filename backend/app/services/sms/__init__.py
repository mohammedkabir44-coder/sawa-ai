"""SMS provider factory."""
import logging

from app.core.config import settings
from app.services.sms.base import SMSProvider
from app.services.sms.mock import MockSMSProvider

logger = logging.getLogger(__name__)


def get_sms_provider() -> SMSProvider:
    """Return the configured SMS provider.

    Controlled by the ``SMS_PROVIDER`` environment variable.
    Real (Nigerian) providers are only used when credentials are present;
    the mock is the safe default for local development and tests.
    """
    provider = settings.SMS_PROVIDER.lower()

    if provider == "nigerian" and settings.SMS_API_KEY:
        try:
            from app.services.sms.nigerian import NigerianSMSProvider

            return NigerianSMSProvider(
                api_key=settings.SMS_API_KEY,
                api_secret=settings.SMS_API_SECRET,
                sender_id=settings.SMS_SENDER_ID,
            )
        except ImportError:
            logger.warning(
                "SMS_PROVIDER=nigerian but the Nigerian SMS provider is "
                "not installed; falling back to MockSMSProvider."
            )

    # Default: clearly-labelled mock provider for development.
    return MockSMSProvider()


__all__ = ["SMSProvider", "get_sms_provider"]