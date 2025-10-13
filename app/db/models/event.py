"""
Event database model.

This module defines the Event model for storing analysis events and results.
Events capture all prompt analysis activity for auditing and analytics.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.rule_trigger import RuleTrigger


class Event(Base):
    """
    Database model for analysis events.

    Events represent individual prompt analysis operations and their results.
    This provides audit trail and analytics capabilities.

    Attributes:
        id: Primary key
        task_id: Optional external task identifier
        prompt: The analyzed prompt text (optional for privacy)
        status: Overall analysis status (allow, block, notify)
        flow_name: Name of the pipeline flow used
        pipeline_results: JSON field with detailed pipeline results
        timestamp: When the analysis occurred
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[Optional[str]] = mapped_column(
        String(255), index=True, nullable=True
    )
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    flow_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    pipeline_results: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relationships
    triggers: Mapped[list["RuleTrigger"]] = relationship(  # noqa: F821
        "RuleTrigger", back_populates="event", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, status='{self.status}', flow='{self.flow_name}', timestamp={self.timestamp})>"
