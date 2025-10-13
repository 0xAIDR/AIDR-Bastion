"""
API endpoints for rule management.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import rule_crud
from app.db.session import get_session
from app.schemas.rule import RuleCreate, RuleList, RuleResponse, RuleUpdate

rules_router = APIRouter(prefix="/rules", tags=["Rules Management"])


@rules_router.post("", response_model=RuleResponse, status_code=201)
async def create_rule(
    rule_in: RuleCreate,
    session: AsyncSession = Depends(get_session),
) -> RuleResponse:
    """
    Create a new detection rule.

    Args:
        rule_in: Rule data
        session: Database session

    Returns:
        Created rule

    Raises:
        HTTPException: If rule with UUID already exists
    """
    # Check if rule with UUID already exists
    existing = await rule_crud.get_by_uuid(session, uuid=rule_in.uuid)
    if existing:
        raise HTTPException(status_code=400, detail=f"Rule with UUID {rule_in.uuid} already exists")

    rule = await rule_crud.create(session, obj_in=rule_in.model_dump())
    return RuleResponse.model_validate(rule)


@rules_router.get("", response_model=RuleList)
async def list_rules(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    category: Optional[str] = Query(None, description="Filter by category"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    session: AsyncSession = Depends(get_session),
) -> RuleList:
    """
    Get list of rules with optional filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum records to return
        category: Optional category filter
        enabled: Optional enabled status filter
        session: Database session

    Returns:
        List of rules with total count
    """
    if category:
        rules = await rule_crud.get_by_category(session, category=category, skip=skip, limit=limit)
    elif enabled is not None:
        if enabled:
            rules = await rule_crud.get_enabled(session, skip=skip, limit=limit)
        else:
            # Get all and filter disabled
            all_rules = await rule_crud.get_multi(session, skip=skip, limit=limit)
            rules = [r for r in all_rules if not r.enabled]
    else:
        rules = await rule_crud.get_multi(session, skip=skip, limit=limit)

    total = await rule_crud.count(session)
    return RuleList(total=total, rules=[RuleResponse.model_validate(r) for r in rules])


@rules_router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: int,
    session: AsyncSession = Depends(get_session),
) -> RuleResponse:
    """
    Get rule by ID.

    Args:
        rule_id: Rule ID
        session: Database session

    Returns:
        Rule details

    Raises:
        HTTPException: If rule not found
    """
    rule = await rule_crud.get(session, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    return RuleResponse.model_validate(rule)


@rules_router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    rule_in: RuleUpdate,
    session: AsyncSession = Depends(get_session),
) -> RuleResponse:
    """
    Update existing rule.

    Args:
        rule_id: Rule ID
        rule_in: Fields to update
        session: Database session

    Returns:
        Updated rule

    Raises:
        HTTPException: If rule not found
    """
    rule = await rule_crud.get(session, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    # Only update provided fields
    update_data = rule_in.model_dump(exclude_unset=True)
    updated_rule = await rule_crud.update(session, db_obj=rule, obj_in=update_data)
    return RuleResponse.model_validate(updated_rule)


@rules_router.delete("/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """
    Delete rule by ID.

    Args:
        rule_id: Rule ID
        session: Database session

    Raises:
        HTTPException: If rule not found
    """
    rule = await rule_crud.delete(session, id=rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")


@rules_router.patch("/{rule_id}/toggle", response_model=RuleResponse)
async def toggle_rule(
    rule_id: int,
    session: AsyncSession = Depends(get_session),
) -> RuleResponse:
    """
    Toggle rule enabled/disabled status.

    Args:
        rule_id: Rule ID
        session: Database session

    Returns:
        Updated rule

    Raises:
        HTTPException: If rule not found
    """
    rule = await rule_crud.toggle_enabled(session, id=rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    return RuleResponse.model_validate(rule)
