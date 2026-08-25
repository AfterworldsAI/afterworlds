"""Component recurrence.

CRD Issue 5d (#137), representation schema ``5d-representation-schema-4``.

``rp_mech_components.recurs`` is how often a component's stated effect repeats,
or NULL when the source states no cadence.

**A distinct axis from duration, not a variant of it.** ``DurationKind`` says
how long an effect lasts; this says how often it happens. Burning's damage —
*"a burning creature or object takes 1d4 Fire damage at the start of each of its
turns"* — repeats without ending, and Suffocation's accrual repeats while a
state holds, so representing either as a duration would assert an end the source
never states. Measured corpus-wide before admitting it: 88 distinct rules across
seven top-level sections state a turn boundary.

Stored as the canonical payload, for the same reason
``rp_mech_components.applies_when`` and ``rp_mech_facts.applies_when`` are: a
later reshaping of the value object is a payload change the schema hash catches,
rather than one table migration per field.

**Additive, with no backfill, deliberately.** NULL is the correct value for every
existing row rather than a placeholder awaiting repair: a component with no
recurrence is exactly a component whose effect the source does not repeat, which
is what every row written before this migration is.

Nothing has ever been persisted under schema 4. The committed accepted artifact
declares schema 3 and is carried forward by a registered lift rather than by a
restamp, and it does not become schema-4 authority until a schema-4 batch is
accepted over it — so this column has no historical rows whose meaning it could
change. Note the difference from ``0029``'s note, which could still say no
accepted oracle existed at all; one does now, and it is precisely the artifact
the zero-movement rule exists to leave untouched.

``rp_mech_components`` is not a retained-evidence table, so as in ``0029`` this
adds no content column inside a re-insert guard and rebuilds no trigger.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0030"
down_revision: str | None = "0029"
branch_labels: str | None = None
depends_on: str | None = None

_COMPONENTS = "rp_mech_components"


def upgrade() -> None:
    with op.batch_alter_table(_COMPONENTS) as batch:
        batch.add_column(sa.Column("recurs", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table(_COMPONENTS) as batch:
        batch.drop_column("recurs")
