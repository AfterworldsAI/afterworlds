"""Option-scoped prose bindings.

CRD Issue 5d (#137), representation schema ``5d-representation-schema-6``.

Governing prose is bound to a component, and that scope is too broad whenever
the source states an exhaustive actor choice and then governs one arm of it.
``Help`` (SRD 5.2.1 pp182-183) is the forced instance: *"you do one of the
following"*, and then *"The GM has final say on whether your assistance is
possible"* — which governs the ability-check arm alone — beside a five-foot
range and a *"that enemy"* coreference that govern the attack-roll arm alone.
Bound at component grain each would silently govern the other arm too, which is
a false statement of scope rather than a lossy one.

Sibling components are not the alternative. Components are conjunctive, so two
of them would assert both benefits apply at once, which the source denies.

``rp_mech_prose_bindings.option_key`` names the ``ComponentOption`` the binding
governs, or the empty string when it governs the whole component. Not nullable,
and the empty string is the *absence* of an option rather than a second null
nobody could distinguish from a blank key — the same spelling
``rp_mech_facts.option_key`` already uses, so the two scopes are read the same
way by anything that joins them.

**Additive, with a server default, and no backfill.** The empty string is the
correct value for every existing row rather than a placeholder awaiting repair:
a binding written before this migration governs its whole component, which is
exactly what the empty key states. The canonical projection payload omits the
key entirely when it is empty, so every binding accepted under schemas 1-5
keeps the byte-identical payload — and therefore the five-element provenance
coordinate — it already had.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0031"
down_revision: str | None = "0030"
branch_labels: str | None = None
depends_on: str | None = None

_BINDINGS = "rp_mech_prose_bindings"


def upgrade() -> None:
    with op.batch_alter_table(_BINDINGS) as batch:
        batch.add_column(
            sa.Column(
                "option_key",
                sa.String(255),
                nullable=False,
                server_default="",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table(_BINDINGS) as batch:
        batch.drop_column("option_key")
