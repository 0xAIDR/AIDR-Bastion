"""
Base class for all database models.

This module provides the declarative base class that all database models
should inherit from. It uses SQLAlchemy's DeclarativeBase for type-safe
model definitions.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all database models.

    All models should inherit from this class to be properly tracked
    by SQLAlchemy's metadata system and to enable Alembic migrations.
    """

    pass
