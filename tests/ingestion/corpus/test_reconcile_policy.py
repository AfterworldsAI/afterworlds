"""Reconciliation + policy application tests — Issue 5c, Components B, D.

Synthetic ledgers exercise policy-bounded exclusion (header/footer excluded;
unanticipated content left unresolved), the represented default, projection
directions (split / aggregate), and policy freezing.
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.models import ContainerType, Disposition, LeafType
from afterworlds.ingestion.corpus.policy import (
    FROZEN_POLICY,
    exclusion_reason_for,
    normalize,
    policy_hash,
)
from afterworlds.ingestion.corpus.reconcile import reconcile
from afterworlds.ingestion.corpus.transform import build_corpus

from .conftest import make_leaf, simple_container, synthetic_ledger

# These reconciliation/policy tests are release-agnostic; any fixed package
# identity suffices for the (now package-scoped) output chunk IDs.
_PKG = "00000000-0000-0000-0000-000000000000"


def test_header_footer_is_excluded_under_policy():
    leaves = [
        make_leaf(1, LeafType.HEADER_FOOTER, "7 System Reference Document 5.2.1", 0, 0),
        make_leaf(1, LeafType.PARAGRAPH, "A rule paragraph.", 40, 1),
    ]
    ledger = synthetic_ledger(leaves, [])
    members = build_corpus(ledger, _PKG)
    recon = reconcile(ledger, members, FROZEN_POLICY)
    by_leaf = {d.leaf_id: d for d in recon.dispositions}
    assert by_leaf[leaves[0].leaf_id].disposition is Disposition.EXCLUDED
    assert by_leaf[leaves[0].leaf_id].exclusion_reason_code == "running_header_footer"
    assert by_leaf[leaves[1].leaf_id].disposition is Disposition.REPRESENTED
    assert recon.unresolved_leaves == 0


def test_represented_is_the_default_for_substantive_content():
    leaves = [make_leaf(1, LeafType.PARAGRAPH, "Substantive rule.", 0, 0)]
    ledger = synthetic_ledger(leaves, [])
    recon = reconcile(ledger, build_corpus(ledger, _PKG), FROZEN_POLICY)
    assert recon.represented_leaves == 1
    assert recon.excluded_leaves == 0
    assert recon.unresolved_leaves == 0


def test_same_leaf_same_package_yields_same_chunk_id():
    """Byte-for-byte deterministic under a fixed release identity (PR #134 P1)."""
    ledger = synthetic_ledger([make_leaf(1, LeafType.PARAGRAPH, "Rule.", 0, 0)], [])
    a = build_corpus(ledger, _PKG).chunks[0].chunk_id
    b = build_corpus(ledger, _PKG).chunks[0].chunk_id
    assert a == b


def test_same_leaf_different_package_yields_different_chunk_id():
    """A new immutable release scopes chunk IDs so identical leaves do not
    collide on the global rp_chunks PK; leaf_id (provenance) stays release
    -independent (PR #134 P1)."""
    ledger = synthetic_ledger([make_leaf(1, LeafType.PARAGRAPH, "Rule.", 0, 0)], [])
    chunk_a = build_corpus(ledger, "pkg-A").chunks[0]
    chunk_b = build_corpus(ledger, "pkg-B").chunks[0]
    assert chunk_a.chunk_id != chunk_b.chunk_id
    # Source-side leaf_id is unchanged across releases.
    assert chunk_a.source_leaf_ids == chunk_b.source_leaf_ids


def test_toc_listing_excluded_only_under_toc_container():
    toc = simple_container("Table of Contents", ContainerType.SECTION)
    leaf = make_leaf(1, LeafType.HEADING, "Combat 12", 0, 0, (toc.container_id,))
    labels = {toc.container_id: toc.label}
    reason = exclusion_reason_for(leaf, labels)
    assert reason is not None and reason.code == "toc_or_index_listing"


def test_one_chunk_per_represented_leaf_and_accounting_balances():
    leaves = [
        make_leaf(1, LeafType.HEADING, "Fireball", 0, 0),
        make_leaf(1, LeafType.PARAGRAPH, "A bright streak flashes.", 9, 1),
        make_leaf(
            1, LeafType.HEADER_FOOTER, "131 System Reference Document 5.2.1", 34, 2
        ),
    ]
    ledger = synthetic_ledger(leaves, [])
    members = build_corpus(ledger, _PKG)
    recon = reconcile(ledger, members, FROZEN_POLICY)
    assert len(members.chunks) == 2  # heading + paragraph; footer excluded
    assert recon.inventoried_leaves == 3
    assert recon.represented_leaves == 2
    assert recon.excluded_leaves == 1
    assert recon.unresolved_leaves == 0


def test_reconciliation_covers_exactly_the_ledger_leaves():
    leaves = [
        make_leaf(1, LeafType.PARAGRAPH, f"Rule {i}.", i * 10, i) for i in range(5)
    ]
    ledger = synthetic_ledger(leaves, [])
    recon = reconcile(ledger, build_corpus(ledger, _PKG), FROZEN_POLICY)
    assert {d.leaf_id for d in recon.dispositions} == {leaf.leaf_id for leaf in leaves}


def test_policy_hash_is_stable_and_covers_reasons_and_roles():
    h1 = policy_hash(FROZEN_POLICY)
    h2 = policy_hash(FROZEN_POLICY)
    assert h1 == h2 and len(h1) == 64
    assert {r.code for r in FROZEN_POLICY.exclusion_reasons}
    assert {r.name for r in FROZEN_POLICY.projection_roles} == {
        "authoritative",
        "attribution_repeat",
    }


def test_normalization_folds_ligatures_and_minus():
    assert normalize("ﬁre−5") == "fire-5"
    assert normalize("a   b\nc") == "a b c"
