"""Why retained prose is retained.

CRD Issue 5d (#137), representation schema ``5d-representation-schema-12`` and
the Owner Decision of 2026-09-16 recorded in ADR-005d.

Prose is retained for one of two reasons. Applying the meaning requires
judgement — that is what ``irreducibility_reason_code`` has always said. Or the
meaning is reducible and no identified code-owned use in play, explanation or
correction needs a separate structured field for it. Schema 11 had a shape only
for the first, so recording the second meant labelling reducible meaning with an
irreducibility code, which is the relabelling the amendment forbids in those
words.

``prose_retention_reason_code`` on ``rp_mech_components`` and
``rp_mech_prose_bindings`` is the second reason's own column, read against its
own closed catalog under the declared ``5d-semantic-policy-*`` version rather
than against the irreducibility vocabulary. Exactly one of the two is stated on
each side, so ``rp_mech_prose_bindings.irreducibility_reason_code`` becomes
nullable: a binding retained for a reducibility reason states no irreducibility
reason rather than a false one. The component column was already nullable,
because a component whose handling is ``STRUCTURED`` states neither.

**Additive, and NULL is the correct value for every existing row.** Nothing has
been persisted under schema 12 — the committed corpus artifact still declares
schema 11 on disk and is one crossing behind, lifted element by element by the
registered ``5d-lift-schema-11-to-12`` rather than restamped. Every row written
before this migration stated an irreducibility reason, and stating no retention
reason beside it is exactly what such a row means. The canonical payload omits
the key when it is unset, so every accepted component payload, prose-binding
payload and five-element provenance coordinate keeps the bytes it already had,
and ``compute_persisted_state_digest`` — which serializes through
``projection_payload`` at each row's own recorded schema version — verifies
unchanged over everything already stored.

**The downgrade refuses rather than invents.** Dropping the two columns is
lossless only while no binding has been retained for a reducibility reason;
restoring ``irreducibility_reason_code`` to ``NOT NULL`` over a binding that
honestly stated none would require inventing an irreducibility claim about
prose that is not irreducible, and there is no value that could be invented
honestly. The batch recreate fails on such a row instead, which is the correct
outcome: a corpus that has crossed into schema 12 is brought back by the
registered lift's inverse, not by a column drop.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0032"
down_revision: str | None = "0031"
branch_labels: str | None = None
depends_on: str | None = None

_COMPONENTS = "rp_mech_components"
_BINDINGS = "rp_mech_prose_bindings"


def _retention_column() -> sa.Column[str]:
    return sa.Column("prose_retention_reason_code", sa.String(64), nullable=True)


def upgrade() -> None:
    with op.batch_alter_table(_COMPONENTS) as batch:
        batch.add_column(_retention_column())
    with op.batch_alter_table(_BINDINGS) as batch:
        batch.add_column(_retention_column())
        batch.alter_column(
            "irreducibility_reason_code",
            existing_type=sa.String(64),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table(_BINDINGS) as batch:
        batch.alter_column(
            "irreducibility_reason_code",
            existing_type=sa.String(64),
            nullable=False,
        )
        batch.drop_column("prose_retention_reason_code")
    with op.batch_alter_table(_COMPONENTS) as batch:
        batch.drop_column("prose_retention_reason_code")
