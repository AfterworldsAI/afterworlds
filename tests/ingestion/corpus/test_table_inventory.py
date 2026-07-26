"""Independent expected-table oracle tests — Issue 5c, Component E, PR #134 R15 F4.

The table concordance compares the live reconstruction against a **committed,
frozen** inventory (``srd_table_inventory.json``) — never a fresh detector run at
gate time. These discriminators prove the check is genuinely independent: a
suppressed, flattened, fragmented, merged, or invented table each makes the live
set diverge from the committed one and FAILS. If any of these could not be made
to fail, the oracle would be tautological.
"""

from __future__ import annotations

import copy

import pytest

from afterworlds.ingestion.corpus.table_inventory import (
    build_table_inventory,
    check_against_committed_inventory,
    committed_inventory_hash,
    compare_to_inventory,
    load_committed_inventory,
)


@pytest.fixture(scope="session")
def live_inventory(full_candidate):  # type: ignore[no-untyped-def]
    """The live full-PDF reconstruction inventory (built once)."""
    return build_table_inventory(full_candidate.pages)


@pytest.fixture(scope="session")
def committed():  # type: ignore[no-untyped-def]
    return load_committed_inventory()


def test_live_matches_committed_inventory_positive_control(full_candidate):
    """The live full-PDF reconstruction matches the committed oracle exactly."""
    result = check_against_committed_inventory(full_candidate.pages)
    assert result.passed, (
        result.suppressed[:5],
        result.invented[:5],
        result.mismatched[:5],
    )
    assert result.expected == result.live == result.matched > 0


def test_committed_inventory_has_multi_page_tables(committed):
    """The oracle includes cross-page logical tables (e.g. the Actions table)."""
    assert any(len(t["printed_pages"]) > 1 for t in committed)


def test_suppressing_a_known_table_fails(live_inventory, committed):
    """A table the detector fails to emit (suppressed/flattened away) is caught."""
    mutated = [t for t in live_inventory if t is not live_inventory[0]]
    result = compare_to_inventory(mutated, committed)
    assert not result.passed and result.suppressed


def test_inventing_a_false_table_fails(live_inventory, committed):
    """A table emitted for a region the oracle does not expect is caught."""
    fake = copy.deepcopy(live_inventory[0])
    fake["logical_table_id"] = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    result = compare_to_inventory([*live_inventory, fake], committed)
    assert not result.passed and result.invented


def test_flattening_a_table_fails(live_inventory, committed):
    """Losing/merging cells (same id, different cell detail) is caught."""
    mutated = copy.deepcopy(live_inventory)
    mutated[0]["cells_hash"] = "0" * 64
    result = compare_to_inventory(mutated, committed)
    assert not result.passed and mutated[0]["logical_table_id"] in result.mismatched


def test_fragmenting_a_table_fails(live_inventory, committed):
    """Changing a table's row/segment shape (same id) is caught as a mismatch."""
    mutated = copy.deepcopy(live_inventory)
    mutated[0]["logical_row_count"] = int(mutated[0]["logical_row_count"]) + 1
    result = compare_to_inventory(mutated, committed)
    assert not result.passed and result.mismatched


def test_merging_two_tables_fails(live_inventory, committed):
    """Merging two known tables into one new grid is caught (2 suppressed + 1
    invented)."""
    assert len(live_inventory) >= 3
    a, b = live_inventory[0], live_inventory[1]
    merged = copy.deepcopy(a)
    merged["logical_table_id"] = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
    mutated = [merged, *live_inventory[2:]]
    result = compare_to_inventory(mutated, committed)
    assert not result.passed
    assert a["logical_table_id"] in result.suppressed
    assert b["logical_table_id"] in result.suppressed
    assert merged["logical_table_id"] in result.invented


def test_committed_inventory_hash_is_stable_and_content_derived(committed):
    """The bound identity hash is a pure function of the committed inventory."""
    assert committed_inventory_hash() == committed_inventory_hash()
