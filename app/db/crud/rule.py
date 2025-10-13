"""
CRUD operations for Rule model.

This module provides CRUD operations specific to rules,
including additional queries like filtering by category, enabled status, etc.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.base import CRUDBase
from app.db.models.rule import Rule


class CRUDRule(CRUDBase[Rule]):
    """
    CRUD operations for Rule model.

    Extends base CRUD with rule-specific operations.
    """

    async def get_by_uuid(self, session: AsyncSession, *, uuid: str) -> Optional[Rule]:
        """
        Get rule by UUID.

        Args:
            session: Async database session
            uuid: Rule UUID

        Returns:
            Rule instance or None
        """
        result = await session.execute(select(Rule).where(Rule.uuid == uuid))
        return result.scalar_one_or_none()

    async def get_by_category(
        self, session: AsyncSession, *, category: str, skip: int = 0, limit: int = 100
    ) -> List[Rule]:
        """
        Get rules by category.

        Args:
            session: Async database session
            category: Rule category
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of rules
        """
        result = await session.execute(
            select(Rule).where(Rule.category == category).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_enabled(
        self, session: AsyncSession, *, skip: int = 0, limit: int = 1000
    ) -> List[Rule]:
        """
        Get all enabled rules.

        Args:
            session: Async database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of enabled rules
        """
        result = await session.execute(
            select(Rule).where(Rule.enabled).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def toggle_enabled(self, session: AsyncSession, *, id: int) -> Optional[Rule]:
        """
        Toggle rule enabled status.

        Args:
            session: Async database session
            id: Rule ID

        Returns:
            Updated rule or None
        """
        rule = await self.get(session, id)
        if rule:
            rule.enabled = not rule.enabled
            session.add(rule)
            await session.flush()
            await session.refresh(rule)
        return rule

    async def get_by_language(
        self, session: AsyncSession, *, language: str, skip: int = 0, limit: int = 100
    ) -> List[Rule]:
        """
        Get rules by language/pattern type.

        Args:
            session: Async database session
            language: Pattern language (e.g., 'llm-regex-pattern')
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of rules
        """
        result = await session.execute(
            select(Rule).where(Rule.language == language).offset(skip).limit(limit)
        )
        return list(result.scalars().all())


# Create singleton instance
rule_crud = CRUDRule(Rule)
