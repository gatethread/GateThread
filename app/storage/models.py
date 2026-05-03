from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Column, Text
from sqlmodel import Field, Relationship, SQLModel

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SessionStatus(enum.StrEnum):
    active = "active"
    compressing = "compressing"
    compressed = "compressed"
    compressed_partial = "compressed_partial"
    closed = "closed"


class FactType(enum.StrEnum):
    decision = "decision"
    constraint = "constraint"
    open_question = "open_question"
    finding = "finding"
    file_reference = "file_reference"
    dependency = "dependency"


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: int | None = Field(default=None, primary_key=True)
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.UTC), nullable=False
    )
    ended_at: datetime | None = Field(default=None, nullable=True)
    project_path: str = Field(nullable=False)
    editor_client_id: str = Field(nullable=False)
    status: SessionStatus = Field(default=SessionStatus.active, nullable=False)
    prompt_count: int = Field(default=0, nullable=False)

    facts: list[Fact] = Relationship(back_populates="session")


# ---------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------


class Fact(SQLModel, table=True):
    __tablename__ = "facts"

    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    project: str = Field(nullable=False, index=True)
    session_id: int = Field(foreign_key="sessions.id", nullable=False, index=True)
    type: FactType = Field(nullable=False)
    text: str = Field(nullable=False)
    files: list[str] | None = Field(default=None, sa_column=Column(ARRAY(Text), nullable=True))
    # vector(768) matches nomic-embed-text output dimensions
    embedding: list[float] | None = Field(
        default=None, sa_column=Column(Vector(768), nullable=True)
    )
    confidence: float = Field(default=1.0, nullable=False)
    superseded_by: UUID | None = Field(
        default=None,
        foreign_key="facts.id",
        nullable=True,
        index=True,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.UTC), nullable=False
    )
    refreshed_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.UTC), nullable=False
    )

    session: Session | None = Relationship(back_populates="facts")


# ---------------------------------------------------------------------------
# File activity
# ---------------------------------------------------------------------------


class FileActivity(SQLModel, table=True):
    __tablename__ = "file_activity"

    id: int | None = Field(default=None, primary_key=True)
    project: str = Field(nullable=False, index=True)
    file_path: str = Field(nullable=False)
    session_id: int = Field(foreign_key="sessions.id", nullable=False, index=True)
    was_read: bool = Field(default=False, nullable=False)
    was_modified: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.UTC), nullable=False
    )


# ---------------------------------------------------------------------------
# Audit Log  (append-only — no updates, no deletes)
# ---------------------------------------------------------------------------


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(datetime.UTC), nullable=False, index=True
    )
    client_id: str = Field(nullable=False, index=True)
    routing_decision: str = Field(nullable=False)  # "local" | "cloud" | "block"
    redaction_categories: str | None = Field(default=None, nullable=True)  # JSON array
