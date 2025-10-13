"""
Database session management.

This module handles the creation of the async database engine and session
factory. It supports both SQLite (for development) and PostgreSQL (for production)
through the DATABASE_URL configuration.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.modules.logger import bastion_logger
from settings import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields:
        AsyncSession: Async database session

    Example:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(Item))
            return result.scalars().all()
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            bastion_logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables.

    This should be called on application startup for development.
    In production, use Alembic migrations instead.
    """
    from app.db.base import Base

    bastion_logger.info("Initializing database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    bastion_logger.info("Database initialized successfully")


async def close_db() -> None:
    """
    Close database connections.

    This should be called on application shutdown.
    """
    await engine.dispose()
    bastion_logger.info("Database connections closed")
