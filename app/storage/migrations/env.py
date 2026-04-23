from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

import yaml
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

# Import all models so their metadata is registered before autogenerate runs.
import app.storage.models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def _load_db_url() -> str:
    """Read the database URL from config.yaml, falling back to the environment."""
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url

    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.yaml")
    if os.path.exists(config_path):
        with open(config_path) as f:
            data = yaml.safe_load(f)
        url = data.get("postgres", {}).get("url")
        if url:
            return url

    raise RuntimeError(
        "Database URL not found. Set DATABASE_URL env var or add postgres.url to config.yaml."
    )


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL script)."""
    url = _load_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    url = _load_db_url()
    connectable = create_async_engine(url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
