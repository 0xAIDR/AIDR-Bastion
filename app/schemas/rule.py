"""
Pydantic schemas for Rule model.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RuleBase(BaseModel):
    """Base schema for Rule."""

    uuid: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Rule name")
    details: str = Field(..., description="Rule description")
    language: str = Field(..., description="Pattern language (e.g., 'llm-regex-pattern')")
    pattern: str = Field(..., description="Detection pattern")
    action: str = Field(..., description="Action to take: 'block' or 'notify'")
    severity: Optional[str] = Field(None, description="Severity level")
    category: Optional[str] = Field(None, description="Rule category")
    cwe_id: Optional[str] = Field(None, description="CWE identifier")
    enabled: bool = Field(True, description="Whether rule is enabled")


class RuleCreate(RuleBase):
    """Schema for creating a rule."""

    pass


class RuleUpdate(BaseModel):
    """Schema for updating a rule."""

    name: Optional[str] = None
    details: Optional[str] = None
    language: Optional[str] = None
    pattern: Optional[str] = None
    action: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    cwe_id: Optional[str] = None
    enabled: Optional[bool] = None


class RuleResponse(RuleBase):
    """Schema for rule response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RuleList(BaseModel):
    """Schema for list of rules."""

    total: int
    rules: list[RuleResponse]
