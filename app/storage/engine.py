from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine(database_url: str, pool_size: int = 10) -> None:
    """Create the async engine and session factory. Call once at startup."""
    global _engine, _session_factory

    _engine = create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=0,  # never exceed pool_size — fail fast instead of queuing
        pool_pre_ping=True,  # discard stale connections before use
        echo=False,
    )

    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,  # keep attribute access after commit without re-querying
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields one session per request, auto-commits on exit."""
    if _session_factory is None:
        raise RuntimeError("Storage engine not initialised. Call init_engine() at startup.")

    async with _session_factory() as session:
        yield session


async def create_all_tables() -> None:
    """Create all tables directly from metadata (test/dev convenience only).

    Production schema changes must go through Alembic migrations.
    """
    if _engine is None:
        raise RuntimeError("Storage engine not initialised. Call init_engine() at startup.")

    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def dispose_engine() -> None:
    """Close all pooled connections. Call on app shutdown."""
    if _engine is not None:
        await _engine.dispose()
