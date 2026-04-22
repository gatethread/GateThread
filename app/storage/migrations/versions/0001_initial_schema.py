"""initial schema: sessions, memory_chunks, audit_log

Revision ID: 0001
Revises:
Create Date: 2026-04-22

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable the pgvector extension. Safe to call when already installed.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("project_path", sqlmodel.AutoString(), nullable=False),
        sa.Column("editor_client_id", sqlmodel.AutoString(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "compressing", "compressed", "closed", name="sessionstatus"),
            nullable=False,
        ),
        sa.Column("prompt_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "memory_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column(
            "chunk_type",
            sa.Enum(
                "fact", "decision", "code_reference", "error", "summary", name="chunktype"
            ),
            nullable=False,
        ),
        sa.Column("summary_text", sqlmodel.AutoString(), nullable=False),
        sa.Column("content_hash", sqlmodel.AutoString(), nullable=False),
        sa.Column("files_referenced", sqlmodel.AutoString(), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memory_chunks_session_id", "memory_chunks", ["session_id"])
    op.create_index("ix_memory_chunks_content_hash", "memory_chunks", ["content_hash"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("client_id", sqlmodel.AutoString(), nullable=False),
        sa.Column("routing_decision", sqlmodel.AutoString(), nullable=False),
        sa.Column("redaction_categories", sqlmodel.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_log_timestamp", "audit_log", ["timestamp"])
    op.create_index("ix_audit_log_client_id", "audit_log", ["client_id"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_index("ix_memory_chunks_content_hash", table_name="memory_chunks")
    op.drop_index("ix_memory_chunks_session_id", table_name="memory_chunks")
    op.drop_table("memory_chunks")
    op.drop_table("sessions")
    op.execute("DROP TYPE IF EXISTS chunktype")
    op.execute("DROP TYPE IF EXISTS sessionstatus")
