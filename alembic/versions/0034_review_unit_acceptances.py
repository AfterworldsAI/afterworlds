"""Who accepted each review unit, when, and as part of which action.

CRD Issue 5d (#137), ADR-005d Decision 2 and the Owner Decision of 2026-09-16.

``rp_mech_review_units`` records what a human read and what they require it to
contain. It does not record that anybody accepted it. For a batch that also
accepted spans, ``rp_mech_acceptances`` carried the reviewer and timestamp by
proximity — same batch, same action — but nothing tied a *unit* to that action,
so a widened inventory would sit beside the accepted one claiming the same
acceptance. And a batch that accepted only review units, which is now a legal
acceptance, writes no ``rp_mech_acceptances`` row at all: its reviewer and
timestamp reached no persisted state whatsoever.

``rp_mech_review_unit_acceptances`` is the exact sibling of
``rp_mech_acceptances`` — one row per accepted unit, naming the unit, the batch,
the reviewer and the time. Same shape, so the two halves of one acceptance are
audited by the same rules rather than by a second mechanism that would
eventually disagree — including ``batch_id``, which is nullable on exactly the
terms it is in ``rp_mech_acceptances``: ``None`` for an individually reviewed
unit, and named for one taken as part of a batch. ``accept_proposal`` always
names the batch it is taking.

**Additive, and no rows is the correct state for every existing projection.**
The seven accepted batches recorded no review inventory, so there is nothing to
have accepted; the canonical evidence payload omits the key entirely when the
ledger states none, and every recorded ``persisted_state_digest`` is unchanged.

**The downgrade refuses rather than invents.** Dropping the table is lossless
only while no unit has been accepted. Once a row exists it is the sole record
that a named human accepted that unit at that time — dropping it would leave an
inventory in ``rp_mech_review_units`` that nobody is recorded as having
accepted, which is precisely the state the table exists to make impossible.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0034"
down_revision: str | None = "0033"
branch_labels: str | None = None
depends_on: str | None = None

_TABLE = "rp_mech_review_unit_acceptances"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column("row_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "projection_uuid",
            sa.String(36),
            sa.ForeignKey("rp_mech_projections.projection_uuid", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("unit_id", sa.String(255), nullable=False, index=True),
        sa.Column("batch_id", sa.String(64), nullable=True, index=True),
        sa.Column("reviewer", sa.String(255), nullable=False),
        sa.Column("accepted_at", sa.String(64), nullable=False),
    )


def downgrade() -> None:
    remaining = (
        op.get_bind()
        .execute(sa.text(f"SELECT COUNT(*) FROM {_TABLE}"))  # noqa: S608 - fixed literal
        .scalar_one()
    )
    if remaining:
        raise RuntimeError(
            f"{_TABLE} holds {remaining} rows: each is the only record that a "
            "named human accepted a review unit at a named time, and dropping "
            "them would leave an accepted inventory nobody is recorded as "
            "having accepted. Remove the review inventory deliberately, then "
            "downgrade."
        )
    op.drop_table(_TABLE)
