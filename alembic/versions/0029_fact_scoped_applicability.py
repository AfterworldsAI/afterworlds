"""Fact-scoped applicability.

CRD Issue 5d (#137), representation schema ``5d-representation-schema-3``.

A component's ``applies_when`` says when the *whole component* applies, which
is too broad whenever the source qualifies only part of what a component
states. Grappled is the forced instance — *"The grappler can drag or carry you
when it moves, but every foot of movement costs it 1 extra foot unless you are
Tiny or two or more sizes smaller than it"* — where the exception attaches to
the surcharge alone and the transport permission is unconditional. Represented
component-wide, a Tiny subject would stop being transportable at all.

``rp_mech_facts.applies_when`` is that condition, or NULL when the fact is
conditioned only by its enclosing component or option.

**On the fact row rather than in a table of its own.** A qualifier is
one-to-at-most-one with a fact, and the fact row already carries the exact
scope it is addressed by — ``record_key``, ``component_key``, ``option_key``,
``fact_key``. A separate table would restate that composite key and make a
dangling qualifier representable in storage, which is precisely the state
validation refuses. Reading it back from the fact row makes a qualifier without
its fact unrepresentable rather than merely invalid.

Stored as the canonical applicability payload, for the same reason
``rp_mech_components.applies_when`` is: a later reshaping of the qualifier is a
payload change caught by the schema hash, not a table migration per field.

**Additive, with no backfill, deliberately.** NULL is the correct value for
every existing fact row rather than a placeholder awaiting repair: a fact with
no qualifier is exactly a fact conditioned only by its enclosing scopes, which
is what every row written before this migration is. No projection can carry a
qualifier yet, because none exists — ``oracles/`` holds no accepted oracle, so
nothing has ever been published under schema 3.

``rp_mech_facts`` is not a retained-evidence table, so unlike ``0028`` this
adds no content column inside a re-insert guard and no trigger is rebuilt.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0029"
down_revision: str | None = "0028"
branch_labels: str | None = None
depends_on: str | None = None

_FACTS = "rp_mech_facts"


def upgrade() -> None:
    with op.batch_alter_table(_FACTS) as batch:
        batch.add_column(sa.Column("applies_when", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table(_FACTS) as batch:
        batch.drop_column("applies_when")
