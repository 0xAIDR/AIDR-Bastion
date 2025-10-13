"""
Rule database model.

This module defines the Rule model for storing detection rules in the database.
Rules can be loaded from YAML files or created dynamically via API.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.rule_trigger import RuleTrigger


class Rule(Base):
    """
    Database model for detection rules.

    Rules define patterns and actions for detecting malicious content.
    They can be loaded from YAML files or managed through the API.

    Attributes:
        id: Primary key
        uuid: Unique identifier from rule definition
        name: Human-readable rule name
        details: Detailed description of what the rule detects
        language: Language/format of the pattern (e.g., 'llm-regex-pattern')
        pattern: The actual detection pattern (regex, code pattern, etc.)
        action: Action to take when rule matches ('block' or 'notify')
        severity: Severity level (critical, high, medium, low)
        category: Rule category (injection, obfuscation, leakage, etc.)
        cwe_id: Common Weakness Enumeration ID if applicable
        enabled: Whether the rule is currently active
        created_at: Timestamp when rule was created
        updated_at: Timestamp when rule was last updated
    """

    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(100), nullable=False)
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False, default="notify")
    severity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cwe_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    triggers: Mapped[list["RuleTrigger"]] = relationship(  # noqa: F821
        "RuleTrigger", back_populates="rule", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Rule(uuid='{self.uuid}', name='{self.name}', action='{self.action}', enabled={self.enabled})>"
