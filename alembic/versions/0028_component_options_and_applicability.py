"""Component applicability and exhaustive actor-choice options.

CRD Issue 5d (#137), representation schema ``5d-representation-schema-2``.

Two structures the schema-1 component could not hold:

* ``rp_mech_components.applies_when`` — the closed applicability qualifier, or
  NULL when the component applies unconditionally. Stored as its canonical
  payload rather than as one column per field, so a later reshaping of the
  qualifier is a payload change checked by the schema hash rather than a table
  migration per field.
* ``rp_mech_component_options`` — one row per option of a component that states
  an exhaustive actor choice. A component that is a conjunction has none.

``rp_mech_facts.option_key`` names the owning option, or ``""`` for a fact held
directly on the component. It is ``NOT NULL`` with an empty-string default
because "no option" is a real, addressable scope: making it nullable would give
the grouping key a third state meaning the same thing as ``""`` and let two
spellings of one scope diverge.

**Additive, with no backfill, deliberately.** Every existing fact row is a
direct fact, and ``""`` is exactly what a direct fact carries — so the server
default is the correct value rather than a placeholder awaiting repair. No
component can have options yet, because no projection built under schema 2
exists: ``oracles/`` holds no accepted oracle, so nothing has ever been
accepted, persisted, or published under the new contract. There is therefore no
prior state to translate and no data-shape decision hidden in this migration.

Revision ID: 0028
Revises: 0027
Create Date: 2026-08-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COMPONENTS = "rp_mech_components"
_FACTS = "rp_mech_facts"
_OPTIONS = "rp_mech_component_options"


def upgrade() -> None:
    with op.batch_alter_table(_COMPONENTS) as batch:
        batch.add_column(sa.Column("applies_when", sa.JSON(), nullable=True))

    with op.batch_alter_table(_FACTS) as batch:
        batch.add_column(
            sa.Column(
                "option_key",
                sa.String(255),
                nullable=False,
                server_default="",
            )
        )

    op.create_table(
        _OPTIONS,
        sa.Column("row_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "projection_uuid",
            sa.String(36),
            sa.ForeignKey("rp_mech_projections.projection_uuid", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("record_key", sa.String(255), nullable=False, index=True),
        sa.Column("component_key", sa.String(255), nullable=False),
        sa.Column("semantic_key", sa.String(255), nullable=False),
        sa.Column("applies_when", sa.JSON(), nullable=True),
        sa.UniqueConstraint(
            "projection_uuid",
            "record_key",
            "component_key",
            "semantic_key",
            name="uq_mech_component_option",
        ),
    )


def downgrade() -> None:
    op.drop_table(_OPTIONS)
    with op.batch_alter_table(_FACTS) as batch:
        batch.drop_column("option_key")
    with op.batch_alter_table(_COMPONENTS) as batch:
        batch.drop_column("applies_when")
