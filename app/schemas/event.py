"""
Pydantic schemas for Event model.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    """Base schema for Event."""

    task_id: Optional[str] = Field(None, description="Task identifier")
    prompt: Optional[str] = Field(None, description="Analyzed prompt")
    status: str = Field(..., description="Analysis status: allow, block, notify")
    flow_name: str = Field(..., description="Pipeline flow name")
    pipeline_results: Optional[dict[str, Any]] = Field(None, description="Pipeline results as JSON")


class EventCreate(EventBase):
    """Schema for creating an event."""

    pass


class EventResponse(EventBase):
    """Schema for event response."""

    id: int
    timestamp: datetime

    model_config = {"from_attributes": True}


class EventList(BaseModel):
    """Schema for list of events."""

    total: int
    events: list[EventResponse]


class EventStats(BaseModel):
    """Schema for event statistics."""

    total: int
    blocked: int
    notified: int
    allowed: int
