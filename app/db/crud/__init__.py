"""
CRUD operations.

This module exports CRUD classes for all models.
"""

from app.db.crud.event import event_crud
from app.db.crud.rule import rule_crud

__all__ = ["rule_crud", "event_crud"]
