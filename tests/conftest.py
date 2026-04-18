# conftest.py — pytest configuration and shared fixtures
#
# This file is automatically loaded by pytest before any tests run.
# Fixtures defined here are available to every test in the suite without
# needing to import them — pytest resolves them by name automatically.
#
# Current fixtures: none yet (app code is not written until Issue #3+)
#
# Fixtures to be added as issues are implemented:
#   - postgres_db    : spins up a test database with a clean schema
#   - redis_client   : connects to a test Redis instance
#   - async_client   : an httpx AsyncClient pointed at the FastAPI test app
#   - mock_ollama    : intercepts Ollama HTTP calls with pre-set responses
#   - mock_litellm   : intercepts LiteLLM calls with pre-set responses

import pytest


# ---------------------------------------------------------------------------
# Event loop configuration for pytest-asyncio
# ---------------------------------------------------------------------------
# pytest-asyncio needs to know what scope the asyncio event loop runs at.
# "session" means one event loop is shared across all async tests in the run.
# This is more efficient than creating a new loop per test and avoids
# resource leak warnings from asyncio.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop_policy():
    """Use the default asyncio event loop policy for the test session."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
