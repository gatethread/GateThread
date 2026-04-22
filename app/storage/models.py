from __future__ import annotations

import enum
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SessionStatus(enum.StrEnum):
    active = "active"
    compressing = "compressing"
    compressed = "compressed"
    closed = "closed"


class ChunkType(enum.StrEnum):
    fact = "fact"
    decision = "decision"
    code_reference = "code_reference"
    error = "error"
    summary = "summary"


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: int | None = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    ended_at: datetime | None = Field(default=None, nullable=True)
    project_path: str = Field(nullable=False)
    editor_client_id: str = Field(nullable=False)
    status: SessionStatus = Field(default=SessionStatus.active, nullable=False)
    prompt_count: int = Field(default=0, nullable=False)

    memory_chunks: list[MemoryChunk] = Relationship(back_populates="session")


# ---------------------------------------------------------------------------
# Memory Chunks
# ---------------------------------------------------------------------------


class MemoryChunk(SQLModel, table=True):
    __tablename__ = "memory_chunks"

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id", nullable=False, index=True)
    chunk_type: ChunkType = Field(nullable=False)
    summary_text: str = Field(nullable=False)
    content_hash: str = Field(nullable=False, index=True)  # SHA-256 of normalised text
    files_referenced: str | None = Field(default=None, nullable=True)  # JSON array of paths
    # vector(768) matches nomic-embed-text output dimensions
    embedding: list[float] | None = Field(
        default=None, sa_column=Column(Vector(768), nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    session: Session | None = Relationship(back_populates="memory_chunks")


# ---------------------------------------------------------------------------
# Audit Log  (append-only — no updates, no deletes)
# ---------------------------------------------------------------------------


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    client_id: str = Field(nullable=False, index=True)
    routing_decision: str = Field(nullable=False)  # "local" | "cloud" | "blocked"
    redaction_categories: str | None = Field(default=None, nullable=True)  # JSON array
