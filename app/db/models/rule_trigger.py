"""
RuleTrigger database model.

This module defines the RuleTrigger model for tracking when rules are triggered.
This provides detailed analytics on rule effectiveness and attack patterns.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.event import Event
    from app.db.models.rule import Rule


class RuleTrigger(Base):
    """
    Database model for rule trigger events.

    Tracks individual instances when a rule matches content.
    Used for statistics, analytics, and understanding attack patterns.

    Attributes:
        id: Primary key
        event_id: Foreign key to Event
        rule_id: Foreign key to Rule
        matched_text: The text that matched the rule (optional excerpt)
        pipeline_name: Name of the pipeline that triggered the rule
        timestamp: When the rule was triggered
    """

    __tablename__ = "rule_triggers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    matched_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pipeline_name: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="triggers")  # noqa: F821
    rule: Mapped["Rule"] = relationship("Rule", back_populates="triggers")  # noqa: F821

    def __repr__(self) -> str:
        return f"<RuleTrigger(id={self.id}, rule_id={self.rule_id}, event_id={self.event_id}, timestamp={self.timestamp})>"
