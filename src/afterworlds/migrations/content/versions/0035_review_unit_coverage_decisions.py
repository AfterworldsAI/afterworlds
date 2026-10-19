"""What a review unit decided about the source it named.

CRD Issue 5d (#137), ADR-005d Decisions 2, 3, 5 and 6 and the Owner Decision of
2026-09-16.

``0033`` recorded which leaves a human read and which rules they required to
have a home. Both halves turned out to be satisfiable by saying nothing. A unit
could name every leaf of a corpus, record no expectation and no exclusion, and
be accepted as complete accounting for all of it — the exact heading, example
and explanation links the span partition used to carry simply disappeared. And
an expectation named a component and a fact family only, so two exceptions of
one family stated in one component were indistinguishable: drop one, and the
survivor answered for both.

Three changes, one obligation.

``rp_mech_review_expectations.source_span_ids`` names the accepted spans the
reviewer read the rule from. It costs nothing to state — they are the spans
already being proposed and accepted — and it is what lets a check ask whether
*this* rule's source text is the text the surviving structure was built from,
rather than whether some fact of the right family is present somewhere in the
component.

``rp_mech_review_groups`` records the other two decisions a reviewer makes
about a coherent stretch: that it supports authority stated elsewhere, naming
what it supports, or that it carries no mechanic, naming why. Group
granularity, as the amendment requires — one row may answer for a whole
coherent group, and nothing here asks for a row per character or per extraction
fragment.

``rp_mech_review_units.excluded_group_reasons`` is dropped because
``rp_mech_review_groups`` replaces it exactly: a reason with no membership
cannot say which text it excused, which was the defect.

**The upgrade refuses rather than inventing.** No accepted artifact carries a
review inventory — every retained proposal declares ``5d-proposal-1``, which
states none — so the correct state for every recorded projection is no rows,
and this migration then does nothing but change shape. Where rows *do* exist
they are a draft built under the older shape, and there is no honest automatic
conversion: an expectation has no recorded source span, and an exclusion reason
has no recorded membership. Supplying either would be this migration inventing
review evidence. Delete the draft projection deliberately, then upgrade.

The downgrade refuses on the same terms and for the reason ``0033`` already
states: once a unit exists, these rows are the only record of what a human
decided about that source.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0035"
down_revision: str | None = "0034"
branch_labels: str | None = None
depends_on: str | None = None

_UNITS = "rp_mech_review_units"
_EXPECTATIONS = "rp_mech_review_expectations"
_GROUPS = "rp_mech_review_groups"


def _refuse_if_populated(direction: str) -> None:
    bind = op.get_bind()
    for table in (_EXPECTATIONS, _UNITS):
        remaining = bind.execute(
            sa.text(f"SELECT COUNT(*) FROM {table}")  # noqa: S608 - fixed literals
        ).scalar_one()
        if remaining:
            raise RuntimeError(
                f"{table} holds {remaining} rows: a recorded review unit is the "
                "only record that a human read that source, and there is no "
                f"honest automatic {direction} of what it decided. Remove the "
                "review inventory deliberately, then run this migration."
            )


def upgrade() -> None:
    _refuse_if_populated("conversion")
    with op.batch_alter_table(_EXPECTATIONS) as batch:
        batch.add_column(sa.Column("source_span_ids", sa.JSON, nullable=False))
    with op.batch_alter_table(_UNITS) as batch:
        batch.drop_column("excluded_group_reasons")
    op.create_table(
        _GROUPS,
        sa.Column("row_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "projection_uuid",
            sa.String(36),
            sa.ForeignKey("rp_mech_projections.projection_uuid", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("unit_id", sa.String(255), nullable=False, index=True),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("leaf_ids", sa.JSON, nullable=False),
        # NULL for the role that does not state them, checked on reconstruction
        # rather than trusted: a supporting group names what it supports, an
        # excluded group states why, and a row carrying both is neither.
        sa.Column("supports_record_key", sa.String(255), nullable=True),
        sa.Column("supports_component_key", sa.String(255), nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
    )


def downgrade() -> None:
    bind = op.get_bind()
    remaining = bind.execute(sa.text(f"SELECT COUNT(*) FROM {_GROUPS}")).scalar_one()
    if remaining:
        raise RuntimeError(
            f"{_GROUPS} holds {remaining} rows: they are the only record of "
            "what a reviewer decided about source that states no rule, and "
            "nothing else can recover them. Remove the review inventory "
            "deliberately, then downgrade."
        )
    _refuse_if_populated("reversal")
    op.drop_table(_GROUPS)
    with op.batch_alter_table(_UNITS) as batch:
        batch.add_column(
            sa.Column("excluded_group_reasons", sa.JSON, nullable=False)
        )
    with op.batch_alter_table(_EXPECTATIONS) as batch:
        batch.drop_column("source_span_ids")
