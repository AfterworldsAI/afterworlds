"""What a reviewer actually read, and what they require it to contain.

CRD Issue 5d (#137), ADR-005d Decisions 2, 3 and 6 and the Owner Decision of
2026-09-16.

Coverage used to mean one thing only: a gap-free tiling of classification spans
over every character of every extracted leaf. That is a real property, but it is
not the property review exists to establish. It cannot tell a leaf that was read
and found to contain three rules from a leaf that was mechanically partitioned
and never read, and it demands character accounting over navigation furniture
and licence text as the price of reviewing a section at all.

``rp_mech_review_units`` records the coherent source boundary — section, entry
or table — that a human reviewed as one whole, with its exact 5c leaf
membership. ``rp_mech_review_expectations`` records what that reviewer requires
to be present afterwards: for each rule they read, the component that must carry
it and, when the rule reduces to structure, the fact family that must hold it. A
NULL ``fact_family`` is the reviewer's judgement that exact governing prose is
the rule's home, so the component must exist and must be prose-bound or mixed.

Expectations are derived from the source and checked *into* the representation.
Nothing here is derived from the representation being tested — an expectation
read back out of the output could never catch an omitted rule, which is the one
thing it exists to do. That is why there is no closure check against the
representation on load, unlike provenance obligations.

**Additive, and no rows is the correct state for every existing projection.**
The seven accepted batches were reviewed and accepted before this shape existed;
they claim no review units, and the canonical payload omits the key entirely
when the inventory is empty, so every recorded projection identity and every
recorded ``persisted_state_digest`` is unchanged. A projection that claims no
units is still held to the complete-partition rule exactly as before — the
relaxation applies only to a leaf an accepted unit actually names.

**The downgrade refuses rather than invents.** Dropping the tables is lossless
only while nothing has been reviewed by unit. Once a unit exists, the rows are
the sole record that a human read that stretch of source and what they required
of it; there is nothing elsewhere to recover them from, and a projection whose
partition was accepted as incomplete *because* a unit vouched for it would
silently become an unreviewed one. So the downgrade drops the tables only when
both are empty and raises otherwise.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0033"
down_revision: str | None = "0032"
branch_labels: str | None = None
depends_on: str | None = None

_UNITS = "rp_mech_review_units"
_EXPECTATIONS = "rp_mech_review_expectations"


def _projection_fk() -> sa.Column[str]:
    return sa.Column(
        "projection_uuid",
        sa.String(36),
        sa.ForeignKey("rp_mech_projections.projection_uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


def upgrade() -> None:
    op.create_table(
        _UNITS,
        sa.Column("row_id", sa.Integer, primary_key=True, autoincrement=True),
        _projection_fk(),
        sa.Column("unit_id", sa.String(255), nullable=False, index=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("leaf_ids", sa.JSON, nullable=False),
        sa.Column("excluded_group_reasons", sa.JSON, nullable=False),
        sa.UniqueConstraint(
            "projection_uuid", "unit_id", name="uq_rp_mech_review_unit_identity"
        ),
    )
    op.create_table(
        _EXPECTATIONS,
        sa.Column("row_id", sa.Integer, primary_key=True, autoincrement=True),
        _projection_fk(),
        sa.Column("unit_id", sa.String(255), nullable=False, index=True),
        sa.Column("record_key", sa.String(255), nullable=False, index=True),
        sa.Column("component_key", sa.String(255), nullable=False),
        sa.Column("fact_family", sa.String(64), nullable=True),
    )


def downgrade() -> None:
    bind = op.get_bind()
    for table in (_EXPECTATIONS, _UNITS):
        remaining = bind.execute(
            sa.text(f"SELECT COUNT(*) FROM {table}")  # noqa: S608 - fixed literals
        ).scalar_one()
        if remaining:
            raise RuntimeError(
                f"{table} holds {remaining} rows: a recorded review unit is the "
                "only record that a human read that source, and dropping it "
                "would leave an accepted partition vouched for by nothing. "
                "Remove the review inventory deliberately, then downgrade."
            )
    op.drop_table(_EXPECTATIONS)
    op.drop_table(_UNITS)
