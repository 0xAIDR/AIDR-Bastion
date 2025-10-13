"""
Base CRUD operations.

This module provides generic CRUD operations that can be inherited
by specific model CRUD classes.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase(Generic[ModelType]):
    """
    Base class for CRUD operations.

    Provides generic create, read, update, delete operations for any model.

    Attributes:
        model: The SQLAlchemy model class
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize CRUD object with model class.

        Args:
            model: SQLAlchemy model class
        """
        self.model = model

    async def get(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID.

        Args:
            session: Async database session
            id: Record ID

        Returns:
            Model instance or None if not found
        """
        result = await session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, session: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.

        Args:
            session: Async database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        result = await session.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(
        self, session: AsyncSession, *, obj_in: Dict[str, Any]
    ) -> ModelType:
        """
        Create a new record.

        Args:
            session: Async database session
            obj_in: Dictionary with model fields

        Returns:
            Created model instance
        """
        db_obj = self.model(**obj_in)
        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self, session: AsyncSession, *, db_obj: ModelType, obj_in: Dict[str, Any]
    ) -> ModelType:
        """
        Update an existing record.

        Args:
            session: Async database session
            db_obj: Existing model instance
            obj_in: Dictionary with fields to update

        Returns:
            Updated model instance
        """
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj

    async def delete(self, session: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """
        Delete a record by ID.

        Args:
            session: Async database session
            id: Record ID

        Returns:
            Deleted model instance or None if not found
        """
        obj = await self.get(session, id)
        if obj:
            await session.delete(obj)
            await session.flush()
        return obj

    async def count(self, session: AsyncSession) -> int:
        """
        Count total records.

        Args:
            session: Async database session

        Returns:
            Total count of records
        """
        result = await session.execute(select(self.model))
        return len(list(result.scalars().all()))
