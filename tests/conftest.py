"""Pytest configuration and async fixtures for Wird API tests."""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.database import async_session_factory, close_db
from app.services.quran_service import QuranService


@pytest_asyncio.fixture(scope="session", autouse=True)
async def warm_test_cache():
    """Ensure in-memory cache is warmed before any test runs."""
    async with async_session_factory() as session:
        await QuranService.warm_cache(session)
    yield
    await close_db()


@pytest_asyncio.fixture
async def client():
    """Async HTTP client targeting the FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
