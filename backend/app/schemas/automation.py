"""Automation schemas (V1 Automation Engine)."""
import json
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# --- Supported triggers & actions for V1 ---
SUPPORTED_TRIGGERS = {
    "whatsapp_message_received",
    "new_lead_created",
    "scheduled_time",
}
SUPPORTED_STEP_TYPES = {"action", "condition", "delay"}
SUPPORTED_ACTIONS = {"send_whatsapp", "send_sms", "wait_delay", "add_tag"}


def _parse_json_dict(value):
    """Accept either a dict or a JSON string (as stored on model columns)."""
    if isinstance(value, str):
        try:
            parsed = json.loads(value or "{}")
            return parsed if isinstance(parsed, dict) else {}
        except (ValueError, TypeError):
            return {}
    return value or {}


class AutomationStepCreate(BaseModel):
    """A single step in an automation workflow.

    * ``step_type`` — ``action`` | ``condition`` | ``delay``
    * ``action_type`` — one of ``send_whatsapp``, ``send_sms``,
      ``wait_delay``, ``add_tag`` (required for ``step_type == "action"``)
    * ``config`` — JSON config, e.g. ``{"hours": 2}`` for a delay or
      ``{"message": "...", "to": "+234..."}`` for a send action.
    * ``order_index`` — execution order (starts at 0).
    """

    step_type: str = Field(pattern="^(action|condition|delay)$")
    action_type: str = Field(default="", max_length=50)
    config: dict = Field(default_factory=dict)
    order_index: int = Field(default=0, ge=0)
    is_enabled: bool = True


class AutomationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=2000)
    trigger_type: str = Field(
        pattern="^(whatsapp_message_received|new_lead_created|scheduled_time)$"
    )
    trigger_config: dict = Field(default_factory=dict)
    is_active: bool = True
    steps: list[AutomationStepCreate] = Field(default_factory=list)


class AutomationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    trigger_type: str | None = Field(
        default=None,
        pattern="^(whatsapp_message_received|new_lead_created|scheduled_time)$",
    )
    trigger_config: dict | None = None
    is_active: bool | None = None
    steps: list[AutomationStepCreate] | None = None


class AutomationStepOut(BaseModel):
    id: int
    automation_id: int
    step_type: str
    action_type: str
    config: dict = Field(default_factory=dict)
    position: int
    is_enabled: bool

    model_config = {"from_attributes": True}

    _normalize_config = field_validator("config", mode="before")(_parse_json_dict)


class AutomationOut(BaseModel):
    id: int
    business_id: int
    name: str
    description: str
    trigger_type: str
    trigger_config: dict = Field(default_factory=dict)
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

    _normalize_trigger_config = field_validator("trigger_config", mode="before")(
        _parse_json_dict
    )


class AutomationDetail(AutomationOut):
    steps: list[AutomationStepOut] = Field(default_factory=list)


class AutomationList(BaseModel):
    items: list[AutomationOut]
    total: int


class AutomationRunOut(BaseModel):
    id: int
    automation_id: int
    trigger_event: str
    status: str
    current_step: int
    error: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}