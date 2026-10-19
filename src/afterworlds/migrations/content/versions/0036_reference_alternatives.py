"""Labelled alternative destinations of a reference.

CRD Issue 5d (#137), representation schema ``5d-representation-schema-17`` and
the Owner Decisions of 2026-10-01 (ADR-005d Decision 7, proposed amendment).

Some source pointers name a destination that differs by class, class level or
the reader's situation. A resolved citation may now fan out into several
labelled alternatives, each naming a record and optionally one of its
components, a situation, a class and a minimum level in that class. These five
columns on ``rp_mech_references`` carry them.

**Additive, and the defaults are the correct value for every existing row.**
Every row written before this migration states one destination at record grain
with no label, situation or class route, which is exactly what ``""``, NULL and
``0`` say. The canonical payload omits each key when it is empty, so every
accepted reference payload and provenance coordinate keeps its bytes, and the
persisted-state digest verifies unchanged over everything already stored.

**The downgrade refuses rather than drops meaning.** Dropping the columns is
lossless only while no row states an alternative; a corpus that has crossed
into schema 17 is brought back by the registered lift's inverse, not by a
column drop.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0036"
down_revision: str | None = "0035"
branch_labels: str | None = None
depends_on: str | None = None

_REFERENCES = "rp_mech_references"
_COLUMNS = (
    "target_component_key",
    "alternative_label",
    "situation",
    "class_record_key",
    "minimum_class_level",
)


def upgrade() -> None:
    with op.batch_alter_table(_REFERENCES) as batch:
        batch.add_column(
            sa.Column(
                "target_component_key",
                sa.String(255),
                nullable=False,
                server_default="",
            )
        )
        batch.add_column(
            sa.Column("alternative_label", sa.Text, nullable=False, server_default="")
        )
        batch.add_column(sa.Column("situation", sa.String(32), nullable=True))
        batch.add_column(
            sa.Column(
                "class_record_key", sa.String(255), nullable=False, server_default=""
            )
        )
        batch.add_column(
            sa.Column(
                "minimum_class_level",
                sa.Integer,
                nullable=False,
                server_default="0",
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    stated = bind.execute(
        sa.text(
            f"SELECT COUNT(*) FROM {_REFERENCES} WHERE target_component_key != '' "
            "OR alternative_label != '' OR situation IS NOT NULL "
            "OR class_record_key != '' OR minimum_class_level != 0"
        )
    ).scalar_one()
    if stated:
        raise RuntimeError(
            f"{stated} reference rows state an alternative destination; "
            "dropping the columns would discard that meaning"
        )
    with op.batch_alter_table(_REFERENCES) as batch:
        for column in reversed(_COLUMNS):
            batch.drop_column(column)
