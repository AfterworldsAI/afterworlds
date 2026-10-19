"""Alembic environment for the remote control store (ADR-021 D5).

A separate migration chain from the content store's ``alembic/``: the control
store is a different database, never restored with a content snapshot.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import engine_from_config, pool

from afterworlds.remote.control_orm import ControlBase

config = context.config
target_metadata = ControlBase.metadata


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
