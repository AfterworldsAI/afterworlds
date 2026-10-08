"""The community-source comparison instrument measures what it claims to.

Step 2 of the Recorded Owner Decision of 21 September 2026 requires the pinned
snapshot to be checked against the official PDF, and requires the result to say
honestly what was checked and what was not. That makes the instrument itself the
thing under test: a comparison that silently normalizes a difference away, or
reports a structural question as answered, would produce a confident number with
no evidence behind it.

The Owner-supplied positive controls are the load-bearing cases here. They are
known-good regions, so whatever they produce is the instrument's own noise, and
the discrepancy threshold has to stay above it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from afterworlds.ingestion.corpus.pdf_source import ExtractedPage
from afterworlds.ingestion.source import community_compare as cc
from afterworlds.ingestion.source import community_tokens as ct

REPO_ROOT = Path(__file__).resolve().parents[3]

#: Pages the named checks cover, extracted once: the Owner's failure families and
#: both positive controls. Restricted so the suite does not re-extract all 364
#: pages; the committed record is the unrestricted run.
NAMED_PAGES = tuple(
    sorted({page for check in cc.NAMED_CHECKS for page in check.printed_pages})
)

EVIDENCE_PATH = (
    REPO_ROOT / "docs/architecture/issue-5c-5d-community-source-coverage.json"
)


@pytest.fixture(scope="module")
def named_evidence(official_pages: list[ExtractedPage]) -> dict[str, object]:
    """One comparison run over the Owner-named pages only.

    The pages come from the session-scoped extraction in ``conftest.py`` so the
    document is read from disk once for the whole package.
    """
    wanted = set(NAMED_PAGES)
    return cc.compare(
        [page for page in official_pages if page.printed_page in wanted],
        cc.community_text(REPO_ROOT),
        pin_commit=cc.pin_commit(REPO_ROOT),
    )


# ---------------------------------------------------------------------------
# Normalization symmetry
# ---------------------------------------------------------------------------


def test_markdown_markup_is_reduced_to_the_text_a_reader_sees() -> None:
    """Tags, entities and link targets are the snapshot's rendering, not content."""
    raw = (
        "## Chain Shirt\n"
        "<table><tr><td>Chain Shirt</td><td>50 GP</td></tr></table>\n"
        "See [the armor table](equipment.md#armor) &mdash; **13** + Dex.\n"
        "<!-- editorial note -->\n"
    )
    text = cc.markdown_text(raw)
    assert "<td>" not in text and "colspan" not in text
    assert "equipment.md" not in text
    assert "editorial note" not in text
    assert "the armor table" in text
    # Cells must not fuse across the tag boundary, or a window would match text
    # that is adjacent in neither source.
    assert "Chain Shirt 50 GP" in " ".join(text.split())


def test_compaction_fuses_adjacent_cells_which_is_why_structure_is_unchecked() -> None:
    """The normalization that makes the comparison work also erases cell bounds.

    Removing whitespace is what lets ``S tr`` match ``Str`` and survives
    hyphenation and column flow — but it also joins one cell's text to the next,
    so a matched window proves character adjacency and nothing about which column
    a value sits in. This is the concrete mechanism behind every named check
    reporting ``table_association_checked: false``; asserting it here keeps that
    disclosure tied to observable behaviour rather than to a comment.
    """
    assert "1350gp" in cc.compact(cc.markdown_text("<td>13</td><td>50 GP</td>"))


def test_bullets_and_footnote_markers_are_dropped_from_both_sides() -> None:
    """A glyph that is markup on one side and literal on the other must go.

    The PDF renders list items with a bullet glyph and marks table footnotes with
    an asterisk; Markdown writes the first as ``-`` and uses the second for
    emphasis. Dropping the set from the Markdown alone made every bulleted list
    and every footnoted table read as absent from the snapshot while all of their
    words were present.
    """
    pdf_side = cc.compact(cc._SHARED_DROP.sub(" ", "• Who raised you? Value*"))
    md_side = cc.compact(cc.markdown_text("- Who raised you? Value*"))
    assert pdf_side == md_side


# ---------------------------------------------------------------------------
# Containment mechanics
# ---------------------------------------------------------------------------


def test_a_window_set_holds_every_substring_of_the_window_length() -> None:
    assert cc.window_set("abcdef", window=4) == {"abcd", "bcde", "cdef"}


def test_text_shorter_than_one_window_yields_no_windows() -> None:
    """A short tail must not be tested more sensitively than the document."""
    assert cc.window_set("abc", window=4) == set()
    assert cc.unmatched_runs("abc", set(), window=4) == []


def test_fully_present_text_produces_no_runs() -> None:
    haystack = cc.window_set("the quick brown fox jumps", window=8)
    assert cc.unmatched_runs("the quick brown fox jumps", haystack, window=8) == []


def test_an_absent_stretch_becomes_one_run_measured_in_characters() -> None:
    """``length`` counts affected characters, not unmatched windows.

    That is what makes a run comparable against the noise floor independently of
    the window size, so changing the window does not silently move the threshold.
    """
    text = "aaaaaaaaXXXXaaaaaaaa"
    haystack = cc.window_set("aaaaaaaa", window=4)
    runs = cc.unmatched_runs(text, haystack, window=4)
    assert len(runs) == 1
    assert "XXXX" in runs[0].excerpt
    # Windows straddling the joint on either side are unmatched too, so the run
    # covers the absent characters plus up to window-1 on each flank.
    assert 4 <= runs[0].length <= 4 + 2 * (4 - 1)


def test_two_separated_absences_are_two_runs() -> None:
    haystack = cc.window_set("aaaaaaaaaaaaaaaaaaaa", window=4)
    runs = cc.unmatched_runs("aaaaaaaaXXaaaaaaaaaaaaYYaaaaaaaa", haystack, window=4)
    assert len(runs) == 2
    assert runs[0].offset < runs[1].offset


def test_a_trailing_absence_is_still_reported() -> None:
    """The final window must be tested; an unterminated run cannot be dropped."""
    haystack = cc.window_set("aaaaaaaa", window=4)
    runs = cc.unmatched_runs("aaaaaaaaXXXX", haystack, window=4)
    assert len(runs) == 1


# ---------------------------------------------------------------------------
# The noise floor is a bound, not a knob
# ---------------------------------------------------------------------------


def test_the_noise_floor_is_derived_from_the_window_size() -> None:
    """One isolated reordering junction cannot produce a run this long.

    When both sources hold the same text but join it differently at a single
    separated point, only the windows straddling that joint are unmatched, so the
    run is at most ``2 * WINDOW - 1``. The bound is not universal -- see
    ``test_two_nearby_junctions_merge_into_a_run_over_the_floor`` -- so the floor
    is a reporting threshold, not a clearance.
    """
    assert cc.NOISE_FLOOR == 2 * cc.WINDOW


def test_a_pure_reordering_stays_under_the_floor() -> None:
    """The bound above, exercised: same text, different join, no absent content."""
    first, second = "a" * 300, "b" * 300
    haystack = cc.window_set(first) | cc.window_set(second)
    runs = cc.unmatched_runs(second + first, haystack)
    assert runs, "the joint itself must be detected"
    assert max(r.length for r in runs) < cc.NOISE_FLOOR


def test_two_nearby_junctions_merge_into_a_run_over_the_floor() -> None:
    """The floor is not a universal bound, and the module must not claim it is.

    Two reordered joints closer together than ``2 * WINDOW`` merge their
    unmatched windows into one run longer than the floor — here 134 characters —
    with the two sides holding exactly the same characters. So a run at or above
    the floor does not prove content is absent, and a run below it does not prove
    content is present: the floor is where reporting starts, not where a
    difference is cleared. This is the counterexample the ``noise_floor``
    docstring and ``noise_floor_derivation`` now state.
    """
    prefix, first, second, suffix = "x" * 100, "a" * 20, "b" * 20, "y" * 100
    original = prefix + first + second + suffix
    reordered = prefix + second + first + suffix
    assert sorted(original) == sorted(reordered), "no character is absent"
    runs = cc.unmatched_runs(reordered, cc.window_set(original))
    assert max(r.length for r in runs) >= cc.NOISE_FLOOR


def test_the_normalization_erases_a_minus_sign() -> None:
    """``compact`` is not content-preserving, which the module now records.

    ``policy.compact`` folds U+2212 to a hyphen and then removes hyphens, so a
    modifier and its negation compare equal. ``policy`` is frozen
    (``nfkc-ws-1``) and is not changed here; what changes is that the instrument
    no longer claims to hide no content, and sign/qualifier differences are an
    explicit pending qualification item.
    """
    assert cc.compact("modifier −2") == cc.compact("modifier 2")
    assert cc.compact("resistance 1d4") != cc.compact("resistance 1d6")
    pending = " ".join(cc.compare([], {}, pin_commit="probe")["pending"])  # type: ignore[arg-type]
    assert "minus sign" in pending and "record ownership" in pending.lower()


def test_the_positive_controls_stay_under_the_floor(
    named_evidence: dict[str, object],
) -> None:
    """The Owner's known-good regions must not read as discrepancies.

    If this fails, the instrument has degraded and the honest response is to
    explain or fix the new artefact — never to raise :data:`NOISE_FLOOR` until
    the controls pass again.
    """
    observed = named_evidence["positive_control_longest_run"]
    assert isinstance(observed, int)
    assert observed < cc.NOISE_FLOOR
    controls = [c for c in _checks(named_evidence) if c["positive_control"]]
    assert len(controls) == 2
    for check in controls:
        assert check["verdict"] == "below_floor_unresolved"
        assert check["runs_over_floor"] == []


def test_the_multiclass_control_matches_the_snapshot_completely(
    named_evidence: dict[str, object],
) -> None:
    """One control page is fully covered, which is what makes the floor credible.

    A threshold defended only by regions that nearly match could be hiding a
    systematic offset. Printed page 26 has no unmatched window at all.
    """
    page = _page(named_evidence, 26)
    assert page["matched"] == page["windows"]
    assert page["longest_run"] == 0


# ---------------------------------------------------------------------------
# What the instrument refuses to claim
# ---------------------------------------------------------------------------


def test_no_named_check_claims_table_association_was_verified(
    named_evidence: dict[str, object],
) -> None:
    """Character adjacency is not row/column association.

    A window containing a Chain Shirt row's characters does not prove the
    snapshot puts 13 in the AC column. Table structure — colspan cells, empty
    cells, repeated ability-grid headers — is a later increment, and nothing here
    may be read as having settled it.
    """
    checks = _checks(named_evidence)
    assert len(checks) == len(cc.NAMED_CHECKS) == 11
    for check in checks:
        assert check["table_association_checked"] is False
    instrument = named_evidence["instrument"]
    assert isinstance(instrument, dict)
    assert instrument["table_association_checked"] is False
    pending = named_evidence["pending"]
    assert isinstance(pending, list)
    assert any("colspan" in str(item) for item in pending)


def test_a_region_under_the_floor_is_not_reported_as_passing(
    named_evidence: dict[str, object],
) -> None:
    """Below the floor the instrument cannot tell an omission from its own noise.

    So the only verdicts are ``discrepancy`` and ``below_floor_unresolved``.
    Neither is a qualification, and no code path produces a word that could be
    read as one.
    """
    verdicts = {str(c["verdict"]) for c in _checks(named_evidence)}
    assert verdicts <= {"discrepancy", "below_floor_unresolved"}
    assert not {v for v in verdicts if "pass" in v or "qualif" in v}


def test_the_community_source_is_recorded_as_qualified_by_review(
    named_evidence: dict[str, object],
) -> None:
    source = named_evidence["community_source"]
    assert isinstance(source, dict)
    assert source["status"] == "qualified"
    review = source["qualification_review"]
    assert review["reviewed_head"] == "b70d016"
    assert review["artifact"] == "source-structure-final-review.md"
    # Qualified is of the bytes. It is not authority and not acceptance.
    assert "rules authority" in review["not_established"]
    assert source["pinned_commit"] == "1b4b99dcb786cdd1a2fb26f8acec1551191f1ca4"


def test_front_matter_is_separated_rather_than_counted_as_missing_rules() -> None:
    """The licence page and the contents index have no Markdown counterpart.

    Counting them as absent content would understate coverage; dropping them
    silently would overstate it. They are declared, excluded from a second
    figure, and still reported.
    """
    assert cc.FRONT_MATTER == (1, 2, 3, 4)


# ---------------------------------------------------------------------------
# Named-check reporting, without needing the PDF
# ---------------------------------------------------------------------------


def _synthetic(page: int, runs: tuple[cc.Run, ...]) -> cc.PageCoverage:
    return cc.PageCoverage(
        printed_page=page,
        chars=1000,
        windows=100,
        matched=100 - len(runs),
        runs=runs,
        first_line="synthetic",
    )


def test_a_run_at_the_floor_is_reported_as_a_discrepancy() -> None:
    """The floor is inclusive: a run of exactly NOISE_FLOOR is reported.

    Reported, not proven absent — the 2 * WINDOW bound is an isolated-junction
    bound, and nearby junctions merge into a longer run than either difference.
    """
    check = cc.NAMED_CHECKS[0]
    run = cc.Run(offset=0, length=cc.NOISE_FLOOR, excerpt="absent text")
    result = cc.check_result(check, {9: _synthetic(9, (run,))})
    assert result["verdict"] == "discrepancy"
    assert result["runs_over_floor"] == [
        {"length": cc.NOISE_FLOOR, "excerpt": "absent text"}
    ]


def test_a_run_below_the_floor_is_not_reported_as_a_discrepancy() -> None:
    check = cc.NAMED_CHECKS[0]
    run = cc.Run(offset=0, length=cc.NOISE_FLOOR - 1, excerpt="junction")
    result = cc.check_result(check, {9: _synthetic(9, (run,))})
    assert result["verdict"] == "below_floor_unresolved"
    assert result["runs_over_floor"] == []


def test_a_check_whose_pages_were_not_compared_reports_no_coverage() -> None:
    """A restricted run must not imply a page was cleared when it was not read."""
    result = cc.check_result(cc.NAMED_CHECKS[0], {})
    assert result["coverage"] == []
    assert result["verdict"] == "below_floor_unresolved"


def test_page_coverage_of_an_empty_page_is_not_a_division_by_zero() -> None:
    page = cc.PageCoverage(
        printed_page=1, chars=0, windows=0, matched=0, runs=(), first_line=""
    )
    assert page.coverage == 1.0
    assert page.longest_run == 0


def test_the_positive_control_floor_ignores_pages_it_was_not_given() -> None:
    assert cc.positive_control_floor({}) == 0
    run = cc.Run(offset=0, length=93, excerpt="junction")
    assert cc.positive_control_floor({9: _synthetic(9, (run,))}) == 93


# ---------------------------------------------------------------------------
# The committed record describes this tree
# ---------------------------------------------------------------------------


def test_the_committed_evidence_describes_the_current_sources() -> None:
    """A stale evidence file is worse than none: it reports a run never made.

    This does not re-run the 364-page comparison. It asserts the committed
    record's header still names this PDF, this pinned commit, and this
    instrument's window and floor — so changing any of them without regenerating
    the record fails here.
    """
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    official = evidence["official_source"]
    assert official["sha256"] == cc.PDF_SHA256
    assert official["pages_compared"] == 364
    assert evidence["community_source"]["pinned_commit"] == cc.pin_commit(REPO_ROOT)
    instrument = evidence["instrument"]
    assert instrument["window_chars"] == cc.WINDOW
    assert instrument["noise_floor_chars"] == cc.NOISE_FLOOR
    assert instrument["module"] == cc.__name__


def test_the_committed_record_reports_coverage_both_with_and_without_front_matter() -> (
    None
):
    """Both figures, so neither the flattering nor the pessimistic one stands alone."""
    coverage = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))["coverage"]
    assert coverage["front_matter_pages"] == list(cc.FRONT_MATTER)
    assert coverage["fraction"] < coverage["fraction_excluding_front_matter"]
    assert coverage["windows"] > coverage["windows_excluding_front_matter"]


def test_the_committed_record_keeps_its_discrepancy_evidence() -> None:
    """A coverage number with no excerpts is not reviewable evidence."""
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    runs = evidence["discrepancies"]["runs"]
    assert runs, "the document is not expected to match perfectly"
    assert evidence["discrepancies"]["runs_over_floor"] == len(runs)
    for run in runs:
        assert run["length"] >= cc.NOISE_FLOOR
        assert run["excerpt"].strip()
        assert isinstance(run["front_matter"], bool)
    # Sorted longest first, so the reviewable material is at the top.
    assert [r["length"] for r in runs] == sorted(
        (r["length"] for r in runs), reverse=True
    )


def _checks(evidence: dict[str, object]) -> list[dict[str, object]]:
    checks = evidence["named_checks"]
    assert isinstance(checks, list)
    return checks


def _page(evidence: dict[str, object], printed: int) -> dict[str, object]:
    for check in _checks(evidence):
        for page in check["coverage"]:  # type: ignore[index]
            if page["printed_page"] == printed:
                return page
    raise AssertionError(f"printed page {printed} was not compared")


def test_the_committed_record_still_matches_a_live_token_pass(
    official_pages: list[ExtractedPage],
) -> None:
    """The one check that fails when the source is edited and the record is not.

    The header test above compares the record against the instrument's own
    constants, and the manifest test compares digests against the files. Both
    still pass if a content file is corrected, its digest updated, and this
    record left describing the source as it was. This re-runs the token pass
    and the number-order pass over the whole document and asserts the committed
    figures are the figures those passes produce now.
    """
    record = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))["qualification"]
    raw = {
        name: (REPO_ROOT / cc.PIN_DIR / name).read_text(encoding="utf-8")
        for name in cc.CONTENT_FILES
    }
    body = [
        row
        for row in ct.inventory(official_pages, raw)
        if row.printed_page not in cc.FRONT_MATTER
    ]
    tokens = record["token_pass"]
    assert len(body) == tokens["body_pages"]
    assert sum(row.quiet for row in body) == tokens["quiet_body_pages"]
    assert sum(sum(row.pdf_only.values()) for row in body) == (
        tokens["pdf_only_tokens_outside_front_matter"]
    )
    assert sum(sum(row.snapshot_only.values()) for row in body) == (
        tokens["snapshot_only_tokens_outside_front_matter"]
    )

    order = ct.number_order(official_pages, raw)
    differing = sorted(
        row.printed_page
        for row in order
        if row.printed_page not in cc.FRONT_MATTER and not row.same_order
    )
    assert (
        differing
        == record["number_order_pass"]["pages_read_because_their_number_order_differs"]
    )
