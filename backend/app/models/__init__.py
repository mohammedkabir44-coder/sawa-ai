"""SQLAlchemy models. Import all models so Alembic and metadata see them."""
from app.models.user import User, BusinessUser, Role
from app.models.business import Business
from app.models.customer import Customer
from app.models.lead import Lead
from app.models.product import Product, Service
from app.models.conversation import Conversation, Message, MessageMedia
from app.models.whatsapp import (
    WhatsAppAccount,
    WhatsAppCampaign,
    WhatsAppEngagement,
    WhatsAppMessage,
    WhatsAppRecipient,
    WhatsAppTemplate,
)
from app.models.sms import SMSAccount, SMSMessage, SMSTemplate
from app.models.campaign import Campaign, CampaignRecipient
from app.models.automation import Automation, AutomationStep, AutomationRun
from app.models.knowledge import KnowledgeBaseEntry
from app.models.ai import AISettings
from app.models.usage import UsageRecord
from app.models.billing import Plan, Subscription, Invoice
from app.models.audit import AuditLog
from app.models.notification import Notification
from app.models.order import Order, OrderItem, OrderStatus

__all__ = [
    "User",
    "BusinessUser",
    "Role",
    "Business",
    "Customer",
    "Lead",
    "Product",
    "Service",
    "Conversation",
    "Message",
    "MessageMedia",
    "WhatsAppAccount",
    "SMSAccount",
    "SMSTemplate",
    "Campaign",
    "CampaignRecipient",
    "Automation",
    "AutomationStep",
    "AutomationRun",
    "KnowledgeBaseEntry",
    "AISettings",
    "UsageRecord",
    "Plan",
    "Subscription",
    "Invoice",
    "AuditLog",
    "Notification",
    "Order",
    "OrderItem",
    "OrderStatus",
]
