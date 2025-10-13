"""
API endpoints for event viewing and analytics.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import event_crud
from app.db.session import get_session
from app.schemas.event import EventList, EventResponse, EventStats

events_router = APIRouter(prefix="/events", tags=["Events & Analytics"])


@events_router.get("", response_model=EventList)
async def list_events(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    status: Optional[str] = Query(None, description="Filter by status (allow/block/notify)"),
    flow_name: Optional[str] = Query(None, description="Filter by flow name"),
    session: AsyncSession = Depends(get_session),
) -> EventList:
    """
    Get list of events with optional filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum records to return
        status: Optional status filter
        flow_name: Optional flow name filter
        session: Database session

    Returns:
        List of events with total count
    """
    if status:
        events = await event_crud.get_by_status(session, status=status, skip=skip, limit=limit)
    elif flow_name:
        events = await event_crud.get_by_flow(session, flow_name=flow_name, skip=skip, limit=limit)
    else:
        events = await event_crud.get_multi(session, skip=skip, limit=limit)

    total = await event_crud.count(session)
    return EventList(total=total, events=[EventResponse.model_validate(e) for e in events])


@events_router.get("/recent", response_model=EventList)
async def get_recent_events(
    limit: int = Query(50, ge=1, le=500, description="Number of recent events"),
    session: AsyncSession = Depends(get_session),
) -> EventList:
    """
    Get most recent events.

    Args:
        limit: Number of events to return
        session: Database session

    Returns:
        List of recent events
    """
    events = await event_crud.get_recent(session, limit=limit)
    total = await event_crud.count(session)
    return EventList(total=total, events=[EventResponse.model_validate(e) for e in events])


@events_router.get("/stats", response_model=EventStats)
async def get_event_stats(
    session: AsyncSession = Depends(get_session),
) -> EventStats:
    """
    Get event statistics.

    Args:
        session: Database session

    Returns:
        Event statistics by status
    """
    total = await event_crud.count(session)
    blocked = await event_crud.count_by_status(session, status="block")
    notified = await event_crud.count_by_status(session, status="notify")
    allowed = await event_crud.count_by_status(session, status="allow")

    return EventStats(total=total, blocked=blocked, notified=notified, allowed=allowed)


@events_router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    session: AsyncSession = Depends(get_session),
) -> EventResponse:
    """
    Get event by ID.

    Args:
        event_id: Event ID
        session: Database session

    Returns:
        Event details

    Raises:
        HTTPException: If event not found
    """
    event = await event_crud.get(session, event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return EventResponse.model_validate(event)


@events_router.get("/task/{task_id}", response_model=EventResponse)
async def get_event_by_task_id(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> EventResponse:
    """
    Get event by task ID.

    Args:
        task_id: Task identifier
        session: Database session

    Returns:
        Event details

    Raises:
        HTTPException: If event not found
    """
    event = await event_crud.get_by_task_id(session, task_id=task_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event with task_id '{task_id}' not found")
    return EventResponse.model_validate(event)
