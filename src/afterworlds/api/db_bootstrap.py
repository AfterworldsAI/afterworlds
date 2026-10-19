"""Applies the repo's Alembic migrations to head -- the product schema bootstrap.

P1 remediation (PR #126 review round 1): ``create_app()`` previously called
``Base.metadata.create_all(engine)`` against whatever ORM modules happened to
already be imported. That skips every Alembic-only DDL statement (append-only
audit triggers on ``entitlement_event``, ``provider_refusal_log``,
``rpg_roll_audit``) and, on a fresh database, can miss tables entirely for ORM
modules (``entitlement.orm``, ``pipeline.provider._refusal_log``,
``persistence.orm.story_bible``, ``persistence.orm.rules_package``,
``persistence.orm.rolling_summary``, ``pipeline.provider._route_config``,
``pipeline.provider.credentials._metadata``) that ``app.py`` never imports at
startup -- ``alembic/env.py`` imports the complete set, ``app.py`` did not.
Running the real migrations is authoritative regardless of Python import
order and restores DB-layer audit-log immutability (Architecture Invariant
11).
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

#: The content Alembic chain, shipped inside the package (#205).
CONTENT_MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations" / "content"


def upgrade_to_head(database_url: str) -> None:
    """Apply every Alembic migration up to head against *database_url*.

    Idempotent: Alembic tracks the applied revision in the ``alembic_version``
    table, so calling this against an already-current database is a no-op.
    """
    config = Config()
    config.set_main_option("script_location", str(CONTENT_MIGRATIONS))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


__all__ = ["upgrade_to_head"]
