from __future__ import annotations

import asyncio
import os
import sys
import inspect
from pathlib import Path
from typing import AsyncIterator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

TEST_DB_PATH = Path(__file__).parent / "data" / "test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{TEST_DB_PATH}")

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402

engine: AsyncEngine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.run_until_complete(engine.dispose())
    loop.close()


async def _prepare_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.drop, checkfirst=True)
        await conn.run_sync(User.__table__.create, checkfirst=True)


@pytest.fixture(scope="session", autouse=True)
def setup_database(event_loop: asyncio.AbstractEventLoop) -> AsyncIterator[None]:
    event_loop.run_until_complete(_prepare_database())
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(scope="session", autouse=True)
def override_get_db(event_loop: asyncio.AbstractEventLoop) -> AsyncIterator[None]:
    async def _get_test_db() -> AsyncIterator[AsyncSession]:
        async with AsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def db_session(event_loop: asyncio.AbstractEventLoop, setup_database: None) -> AsyncIterator[AsyncSession]:
    session = AsyncSessionLocal()
    yield session
    event_loop.run_until_complete(session.rollback())
    event_loop.run_until_complete(session.close())


@pytest.fixture()
def async_client(event_loop: asyncio.AbstractEventLoop, setup_database: None) -> AsyncIterator[AsyncClient]:
    client = event_loop.run_until_complete(AsyncClient(app=app, base_url="http://test").__aenter__())
    yield client
    event_loop.run_until_complete(client.aclose())


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    testfunction = pyfuncitem.obj
    if inspect.iscoroutinefunction(testfunction):
        loop = pyfuncitem.funcargs.get("event_loop") or asyncio.new_event_loop()
        try:
            allowed_args = {
                name: value
                for name, value in pyfuncitem.funcargs.items()
                if name in inspect.signature(testfunction).parameters
            }
            loop.run_until_complete(testfunction(**allowed_args))
        finally:
            if not pyfuncitem.funcargs.get("event_loop"):
                loop.close()
        return True
    return None
