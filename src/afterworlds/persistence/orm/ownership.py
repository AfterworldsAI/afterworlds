"""Content-store ownership rows -- prerequisite #205 (ADR-021 D5/D7).

``account_resources`` is the durable hosted-account relation for remote Story
roots; it lives beside the Stories it owns so a Story and its ownership commit
in one transaction. It is not FK-bound to ``stories``: the mapping must remain
enumerable for an account after parent rows are detached (#205 §2). Child
records (Arcs ... Turns, Story Bible, sessions, RPG state, Retrieval markers)
are owned through their Story root.

``remote_store_marker`` binds a content store to its remote deployment; a store
without it is never served remotely. Neither table is written by a local
deployment.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class AccountResourceORM(Base):
    """Account-owned resource mapping (matrix: account-owned resource mapping)."""

    __tablename__ = "account_resources"
    __table_args__ = (
        sa.UniqueConstraint("resource_type", "resource_id", "ownership_revision"),
        sa.Index("ix_account_resources_account", "account_id", "resource_type"),
    )

    mapping_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    # "story"
    resource_type: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    resource_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    ownership_revision: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    retired_at: Mapped[str | None] = mapped_column(sa.String(64))
    source_operation_ref: Mapped[str] = mapped_column(sa.String(36), nullable=False)


class RemoteStoreMarkerORM(Base):
    """Singleton marker: this content store was initialized for remote use."""

    __tablename__ = "remote_store_marker"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    content_store_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    initialized_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
