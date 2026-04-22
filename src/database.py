"""Async SQLAlchemy database setup."""
import os
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Create async engine
_engine = None
_async_session_maker = None


def get_database_url() -> str:
    """Get database URL from environment or default."""
    return os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")


def init_engine(database_url: str | None = None):
    """Initialize the async engine and session maker."""
    global _engine, _async_session_maker

    if database_url is None:
        database_url = get_database_url()

    # Convert sqlite:/// to sqlite+aiosqlite:///
    if database_url.startswith("sqlite:///"):
        database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

    _engine = create_async_engine(
        database_url,
        echo=False,
        future=True,
    )

    _async_session_maker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


def get_engine():
    """Get the async engine."""
    global _engine
    if _engine is None:
        init_engine()
    return _engine


def get_session_maker():
    """Get the async session maker."""
    global _async_session_maker
    if _async_session_maker is None:
        init_engine()
    return _async_session_maker


async def get_session() -> AsyncSession:
    """Get a new async session."""
    session_maker = get_session_maker()
    return session_maker()


@asynccontextmanager
async def session_context():
    """Async context manager for database sessions."""
    session = await get_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db():
    """Initialize database tables."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None