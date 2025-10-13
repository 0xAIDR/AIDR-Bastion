"""
CRUD operations for Event model.

This module provides CRUD operations specific to events,
including filtering by status, flow, time ranges, etc.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.base import CRUDBase
from app.db.models.event import Event


class CRUDEvent(CRUDBase[Event]):
    """
    CRUD operations for Event model.

    Extends base CRUD with event-specific operations.
    """

    async def get_by_task_id(
        self, session: AsyncSession, *, task_id: str
    ) -> Optional[Event]:
        """
        Get event by task ID.

        Args:
            session: Async database session
            task_id: Task identifier

        Returns:
            Event instance or None
        """
        result = await session.execute(select(Event).where(Event.task_id == task_id))
        return result.scalar_one_or_none()

    async def get_by_status(
        self, session: AsyncSession, *, status: str, skip: int = 0, limit: int = 100
    ) -> List[Event]:
        """
        Get events by status.

        Args:
            session: Async database session
            status: Event status (allow, block, notify)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of events
        """
        result = await session.execute(
            select(Event)
            .where(Event.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(Event.timestamp.desc())
        )
        return list(result.scalars().all())

    async def get_by_flow(
        self, session: AsyncSession, *, flow_name: str, skip: int = 0, limit: int = 100
    ) -> List[Event]:
        """
        Get events by flow name.

        Args:
            session: Async database session
            flow_name: Pipeline flow name
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of events
        """
        result = await session.execute(
            select(Event)
            .where(Event.flow_name == flow_name)
            .offset(skip)
            .limit(limit)
            .order_by(Event.timestamp.desc())
        )
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        session: AsyncSession,
        *,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Event]:
        """
        Get events within date range.

        Args:
            session: Async database session
            start_date: Start of date range
            end_date: End of date range
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of events
        """
        result = await session.execute(
            select(Event)
            .where(Event.timestamp >= start_date, Event.timestamp <= end_date)
            .offset(skip)
            .limit(limit)
            .order_by(Event.timestamp.desc())
        )
        return list(result.scalars().all())

    async def get_recent(
        self, session: AsyncSession, *, limit: int = 50
    ) -> List[Event]:
        """
        Get most recent events.

        Args:
            session: Async database session
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        result = await session.execute(
            select(Event).order_by(Event.timestamp.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(self, session: AsyncSession, *, status: str) -> int:
        """
        Count events by status.

        Args:
            session: Async database session
            status: Event status

        Returns:
            Count of events
        """
        result = await session.execute(select(Event).where(Event.status == status))
        return len(list(result.scalars().all()))


# Create singleton instance
event_crud = CRUDEvent(Event)
