from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from datetime import datetime, timezone

engine = create_engine('sqlite:///./.venv/sawa_dev.db')

metadata = MetaData()

def utcnow():
    return datetime.now(timezone.utc)

# Business table
businesses = Table(
    'businesses', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(255), nullable=False),
    Column('business_type', String(100), default=''),
    Column('description', Text, default=''),
    Column('location', String(255), default=''),
    Column('phone', String(50), default=''),
    Column('email', String(255), default=''),
    Column('website', String(255), default=''),
    Column('primary_language', String(20), default='en'),
    Column('currency', String(10), default='NGN'),
    Column('timezone', String(50), default='Africa/Lagos'),
    Column('status', String(20), default='active'),
    Column('onboarding_completed', Boolean, default=False),
    Column('created_at', DateTime, default=utcnow),
    Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
)

# Users table
users = Table(
    'users', metadata,
    Column('id', Integer, primary_key=True),
    Column('email', String(255), unique=True, index=True, nullable=False),
    Column('full_name', String(255), nullable=False),
    Column('phone', String(50), default=''),
    Column('password_hash', String(255), nullable=False),
    Column('is_platform_admin', Boolean, default=False),
    Column('is_active', Boolean, default=True),
    Column('created_at', DateTime, default=utcnow),
    Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
)

# Roles table
roles = Table(
    'roles', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(50), unique=True, nullable=False),
    Column('description', String(255), default=''),
    Column('is_system', Boolean, default=False),
    Column('created_at', DateTime, default=utcnow)
)

# Business users table
business_users = Table(
    'business_users', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('role_id', Integer, ForeignKey('roles.id'), nullable=False),
    Column('permissions', String(1000), default=''),
    Column('is_active', Boolean, default=True),
    Column('created_at', DateTime, default=utcnow)
)

# Customers table
customers = Table(
    'customers', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('name', String(255), default=''),
    Column('phone', String(50), index=True, nullable=False),
    Column('email', String(255), default=''),
    Column('preferred_language', String(20), default='unknown'),
    Column('tags', String(500), default=''),
    Column('source', String(50), default='whatsapp'),
    Column('notes', Text, default=''),
    Column('lead_status', String(30), default='new'),
    Column('last_interaction', DateTime, nullable=True),
    Column('created_at', DateTime, default=utcnow, index=True),
    Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
)

# Leads table
leads = Table(
    'leads', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('customer_id', Integer, ForeignKey('customers.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('source', String(50), default='whatsapp'),
    Column('product_id', Integer, ForeignKey('products.id', ondelete='SET NULL'), nullable=True),
    Column('estimated_value', Float, default=0.0),
    Column('currency', String(10), default='NGN'),
    Column('notes', Text, default=''),
    Column('assigned_staff_id', Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    Column('stage', String(30), default='new', index=True),
    Column('last_contact', DateTime, nullable=True),
    Column('next_follow_up', DateTime, nullable=True),
    Column('created_at', DateTime, default=utcnow, index=True),
    Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
)

# Products table
products = Table(
    'products', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('name', String(255), nullable=False),
    Column('description', Text, default=''),
    Column('price', Float, default=0.0),
    Column('currency', String(10), default='NGN'),
    Column('sku', String(100), default=''),
    Column('category', String(100), default=''),
    Column('stock', Integer, default=0),
    Column('availability', String(30), default='available'),
    Column('images', Text, default=''),
    Column('location', String(255), default=''),
    Column('additional_info', Text, default=''),
    Column('is_active', Boolean, default=True),
    Column('created_at', DateTime, default=utcnow),
    Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
)

# Services table
services = Table(
    'services', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('name', String(255), nullable=False),
    Column('description', Text, default=''),
    Column('price', Float, default=0.0),
    Column('currency', String(10), default='NGN'),
    Column('duration', String(100), default=''),
    Column('category', String(100), default=''),
    Column('availability', String(30), default='available'),
    Column('is_active', Boolean, default=True),
    Column('created_at', DateTime, default=utcnow),
    Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
)

# Conversations table
conversations = Table(
    'conversations', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('customer_id', Integer, ForeignKey('customers.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('channel', String(20), default='whatsapp'),
    Column('mode', String(20), default='AI_ACTIVE'),
    Column('language', String(20), default='unknown'),
    Column('lead_status', String(30), default='new'),
    Column('assigned_staff_id', Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    Column('last_message', Text, default=''),
    Column('last_activity', DateTime, default=utcnow, index=True),
    Column('is_unread', Boolean, default=True),
    Column('created_at', DateTime, default=utcnow),
    Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
)

# Messages table
messages = Table(
    'messages', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('conversation_id', Integer, ForeignKey('conversations.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('direction', String(10), nullable=False),
    Column('channel', String(20), default='whatsapp'),
    Column('sender', String(50), default=''),
    Column('body', Text, default=''),
    Column('message_type', String(30), default='text'),
    Column('language', String(20), default='unknown'),
    Column('intent', String(40), default='unknown'),
    Column('intent_confidence', Float, default=0.0),
    Column('transcription', Text, default=''),
    Column('status', String(30), default='received'),
    Column('provider_message_id', String(255), default=''),
    Column('is_ai_generated', Boolean, default=False),
    Column('ai_failed', Boolean, default=False),
    Column('created_at', DateTime, default=utcnow, index=True)
)

# MessageMedia table
message_media = Table(
    'message_media', metadata,
    Column('id', Integer, primary_key=True),
    Column('message_id', Integer, ForeignKey('messages.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('media_type', String(30), default=''),
    Column('provider_media_id', String(255), default=''),
    Column('mime_type', String(100), default=''),
    Column('local_path', String(500), default=''),
    Column('transcription', Text, default=''),
    Column('transcription_confidence', Float, default=0.0),
    Column('created_at', DateTime, default=utcnow)
)

# WhatsApp accounts table
whatsapp_accounts = Table(
    'whatsapp_accounts', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('phone_number', String(50), nullable=False),
    Column('phone_number_id', String(255), default=''),
    Column('business_account_id', String(255), default=''),
    Column('display_name', String(255), default=''),
    Column('is_connected', Boolean, default=False),
    Column('is_default', Boolean, default=False),
    Column('created_at', DateTime, default=utcnow)
)

# SMS accounts table
sms_accounts = Table(
    'sms_accounts', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('sender_id', String(50), default='SAWA'),
    Column('is_configured', Boolean, default=False),
    Column('created_at', DateTime, default=utcnow)
)

# SMS templates table
sms_templates = Table(
    'sms_templates', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('name', String(255), nullable=False),
    Column('body', Text, nullable=False),
    Column('language', String(20), default='en'),
    Column('created_at', DateTime, default=utcnow)
)

# Campaigns table
campaigns = Table(
    'campaigns', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('name', String(255), nullable=False),
    Column('channel', String(30), default='whatsapp'),
    Column('audience', Text, default='{}'),
    Column('message', Text, default=''),
    Column('language', String(20), default='en'),
    Column('schedule_at', DateTime, nullable=True),
    Column('status', String(20), default='draft', index=True),
    Column('is_ai_generated', Boolean, default=False),
    Column('ai_prompt', Text, default=''),
    Column('approved', Boolean, default=False),
    Column('approved_by', Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    Column('approved_at', DateTime, nullable=True),
    Column('created_by', Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    Column('created_at', DateTime, default=utcnow),
    Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
)

# Campaign recipients table
campaign_recipients = Table(
    'campaign_recipients', metadata,
    Column('id', Integer, primary_key=True),
    Column('campaign_id', Integer, ForeignKey('campaigns.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('customer_id', Integer, ForeignKey('customers.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('phone', String(50), nullable=False),
    Column('status', String(30), default='pending'),
    Column('provider_message_id', String(255), default=''),
    Column('error', Text, default=''),
    Column('sent_at', DateTime, nullable=True),
    Column('created_at', DateTime, default=utcnow)
)

# Automations table
automations = Table(
    'automations', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('name', String(255), nullable=False),
    Column('description', Text, default=''),
    Column('trigger_type', String(50), nullable=False),
    Column('trigger_config', Text, default='{}'),
    Column('is_active', Boolean, default=True),
    Column('created_by', Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    Column('created_at', DateTime, default=utcnow),
    Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
)

# Automation steps table
automation_steps = Table(
    'automation_steps', metadata,
    Column('id', Integer, primary_key=True),
    Column('automation_id', Integer, ForeignKey('automations.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('step_type', String(30), nullable=False),
    Column('action_type', String(50), default=''),
    Column('config', Text, default='{}'),
    Column('position', Integer, default=0),
    Column('is_enabled', Boolean, default=True),
    Column('created_at', DateTime, default=utcnow)
)

# Automation runs table
automation_runs = Table(
    'automation_runs', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('automation_id', Integer, ForeignKey('automations.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('trigger_event', String(50), default=''),
    Column('context', Text, default='{}'),
    Column('status', String(20), default='pending'),
    Column('current_step', Integer, default=0),
    Column('error', Text, default=''),
    Column('resume_at', DateTime, nullable=True),
    Column('created_at', DateTime, default=utcnow),
    Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
)

# Knowledge base table
knowledge_base = Table(
    'knowledge_base', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('category', String(50), default='faq'),
    Column('title', String(255), default=''),
    Column('content', Text, default=''),
    Column('language', String(20), default='en'),
    Column('is_active', Boolean, default=True),
    Column('created_at', DateTime, default=utcnow),
    Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
)

# AI settings table
ai_settings = Table(
    'ai_settings', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('provider', String(20), default='mock'),
    Column('model_config', Text, default='{}'),
    Column('created_at', DateTime, default=utcnow),
    Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
)

# Usage table
usage = Table(
    'usage', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('monthly_ai_messages', Integer, default=0),
    Column('monthly_sms', Integer, default=0),
    Column('monthly_whatsapp_messages', Integer, default=0),
    Column('active_automations', Integer, default=0),
    Column('customers', Integer, default=0),
    Column('staff_members', Integer, default=0),
    Column('current_period_start', DateTime, default=utcnow),
    Column('current_period_end', DateTime, default=lambda: datetime.now(timezone.utc).replace(day=1) if datetime.now(timezone.utc).day == 1 else datetime.now(timezone.utc).replace(day=1, month=datetime.now(timezone.utc).month+1)),
    Column('created_at', DateTime, default=utcnow),
    Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
)

# Subscriptions table
subscriptions = Table(
    'subscriptions', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('plan_type', String(20), default='free'),
    Column('status', String(20), default='active'),
    Column('start_date', DateTime, default=utcnow),
    Column('end_date', DateTime, nullable=True),
    Column('created_at', DateTime, default=utcnow),
    Column('updated_at', DateTime, default=utcnow, onupdate=utcnow)
)

# Audit logs table
audit_logs = Table(
    'audit_logs', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='SET NULL'), nullable=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    Column('action', String(100), nullable=False),
    Column('details', Text, default=''),
    Column('ip_address', String(45), nullable=True),
    Column('created_at', DateTime, default=utcnow)
)

# Notifications table
notifications = Table(
    'notifications', metadata,
    Column('id', Integer, primary_key=True),
    Column('business_id', Integer, ForeignKey('businesses.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    Column('title', String(255), nullable=False),
    Column('message', Text, default=''),
    Column('type', String(50), default='info'),
    Column('is_read', Boolean, default=False),
    Column('created_at', DateTime, default=utcnow)
)

# Create all tables
metadata.create_all(engine)
print('All tables created successfully!')