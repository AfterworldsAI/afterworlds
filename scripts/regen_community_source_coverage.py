"""Regenerate the pinned community source's full-coverage evidence record.

    venv/Scripts/python.exe scripts/regen_community_source_coverage.py

Writes ``docs/architecture/issue-5c-5d-community-source-coverage.json``.

The record has two halves. The first is whatever
:func:`community_compare.run` reports, unedited: a character-window comparison
of all 364 official pages against the pinned snapshot, with its own honest list
of what that instrument cannot see. The second is ``qualification``, which is
where those items are answered — by the token pass, by reading the numbers in
order, by the official table of contents, and by the structural checks that
:mod:`tests.ingestion.source.test_community_source_structure` asserts.

Neither half is a verdict on its own. A page is worth reading unless both
passes are quiet on it, and this script reports what is left after both.

``qualification["scope"]`` separates the two kinds of figure the record holds.
A scan is mechanical and covers the whole source, so its count is a count of
everything there is. A read is a person or a named test looking at particular
places, so its count is a count of what was looked at. Reporting them together
would let the breadth of the scans stand in for the depth of the reads.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from afterworlds.ingestion.corpus.pdf_source import extract_pages
from afterworlds.ingestion.corpus.policy import compact
from afterworlds.ingestion.source import community_compare as cc
from afterworlds.ingestion.source import community_tokens as ct

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/architecture/issue-5c-5d-community-source-coverage.json"
COMMAND = "venv/Scripts/python.exe scripts/regen_community_source_coverage.py"

_TABLE = re.compile(r"<table>(.*?)</table>", re.S)
_ROW = re.compile(r"<tr>(.*?)</tr>", re.S)
_CELL = re.compile(r"<t[dh]\b([^>]*)>(.*?)</t[dh]>", re.S)
_COLSPAN = re.compile(r'colspan="(\d+)"')
_TAG = re.compile(r"<[^>]+>")
# A byte-order mark survives utf-8 decoding as a character, so spells.md
# opens with "﻿# Spells" and an anchored ^# missed that one heading.
_HEADING = re.compile(r"^﻿?(#{1,6})\s+(.*)$", re.M)
ABILITIES = ("STR", "DEX", "CON", "INT", "WIS", "CHA")
MINUS = "−"
_SIGNED = re.compile(f"[+{MINUS}-]?" + r"\d+")


def cells(row_body: str) -> list[str]:
    return [_TAG.sub("", body).strip() for _attrs, body in _CELL.findall(row_body)]


def structure(raw: dict[str, str]) -> dict[str, object]:
    """Table shape, ability-grid shape, and the score-to-modifier arithmetic."""
    tables = ragged = grids = rows = triples = 0
    malformed: list[str] = []
    wrong: list[str] = []
    for name, text in raw.items():
        for table in _TABLE.finditer(text):
            tables += 1
            widths = {
                sum(
                    int(span.group(1)) if (span := _COLSPAN.search(attrs)) else 1
                    for attrs, _body in _CELL.findall(row)
                )
                for row in _ROW.findall(table.group(1))
            }
            if len(widths) > 1:
                ragged += 1
            if "<th>MOD</th>" in table.group(1):
                grids += 1
        for row in _ROW.finditer(text):
            cell = cells(row.group(1))
            if len(cell) != 12 or cell[0].upper() not in ABILITIES:
                continue
            rows += 1
            line = text.count("\n", 0, row.start()) + 1
            for i in (0, 4, 8):
                label, score, modifier, save = cell[i : i + 4]
                shaped = (
                    label.upper() in ABILITIES
                    and re.fullmatch(r"\d+", score)
                    and _SIGNED.fullmatch(modifier)
                    and _SIGNED.fullmatch(save)
                    and modifier[0] in f"+{MINUS}-"
                    and save[0] in f"+{MINUS}-"
                )
                if not shaped:
                    malformed.append(f"{name}:{line} {cell}")
                if not (re.fullmatch(r"\d+", score) and _SIGNED.fullmatch(modifier)):
                    continue
                triples += 1
                if int(modifier.replace(MINUS, "-")) != (int(score) - 10) // 2:
                    wrong.append(f"{name}:{line} {label} {score} {modifier}")
    return {
        "tables": tables,
        "ragged_tables": ragged,
        "ability_grids": grids,
        "ability_rows": rows,
        "ability_rows_not_in_label_score_mod_save_shape": sorted(set(malformed)),
        "score_to_modifier_triples": triples,
        "score_to_modifier_mismatches": wrong,
    }


def record_ownership(raw: dict[str, str]) -> dict[str, object]:
    """Which entry each embedded stat block belongs to, read off heading depth.

    Neither comparison pass sees a heading mark: the token pass compares bags
    of words and the number pass compares sequences of numbers, and ``#`` is
    neither. So a stat block emitted at its owning entry's depth reads as
    identical content to both, while in Markdown it has ended that entry and
    captured every entry after it. This reads the depths directly.

    A block is found by its own body carrying both ``**AC**`` and ``**HP**``,
    which no prose paragraph does, so the set is found rather than listed.

    What is reported is each block's own depth and the depth of the entry it
    resolves to, per block. An earlier version of this function also reported a
    count of blocks at or above their owner's depth; that count could only ever
    be zero, because the owner is selected as the nearest preceding heading
    *shallower* than the block, so no selected owner can be at or below it. The
    tautology is removed rather than reworded: the evidence for family G is the
    named blocks in the corrections notes and the independent review of the
    official pages, not a counter that cannot fail.
    """
    heads = {
        name: [
            (text.count("\n", 0, m.start()) + 1, len(m.group(1)), m.group(2).strip())
            for m in _HEADING.finditer(text)
        ]
        for name, text in raw.items()
    }
    blocks: list[dict[str, object]] = []
    for name, found in heads.items():
        lines = raw[name].split("\n")
        for index, (at, depth, title) in enumerate(found):
            end = found[index + 1][0] - 1 if index + 1 < len(found) else len(lines)
            body = "\n".join(lines[at:end])
            if "**AC**" not in body or "**HP**" not in body:
                continue
            owner = next(
                ((od, ot) for _a, od, ot in reversed(found[:index]) if od < depth),
                None,
            )
            blocks.append(
                {
                    "file": name,
                    "line": at,
                    "depth": depth,
                    "title": title,
                    "owner": owner[1] if owner else None,
                    "owner_depth": owner[0] if owner else None,
                }
            )
    record_depths = {
        name: sorted({int(b["depth"]) for b in blocks if b["file"] == name})
        for name in sorted({str(b["file"]) for b in blocks})
    }
    return {
        "why": (
            "A heading closes every open section at its own depth or above, so "
            "depth is the whole of what Markdown says about which entry a "
            "record belongs to. Neither comparison pass reads a heading mark."
        ),
        "does_not_establish": (
            "that a block's owner is the right one. This reports the depths "
            "each block and its resolved owner carry; which entry the official "
            "document places a block under is read from the page, and the six "
            "corrected blocks are named in the corrections notes."
        ),
        "stat_blocks": len(blocks),
        "stat_block_depths_per_file": record_depths,
        "embedded_in_a_non_creature_entry": [
            b for b in blocks if b["file"] not in ("animals.md", "monsters-A-Z.md")
        ],
        "blocks_without_an_owning_entry": [
            b for b in blocks if b["owner_depth"] is None
        ],
        "asserted_by": "tests.ingestion.source.test_community_source_structure",
    }


def headings(raw: dict[str, str]) -> dict[str, object]:
    per_file = {name: _HEADING.findall(text) for name, text in raw.items()}
    return {
        "per_file": {name: len(found) for name, found in per_file.items()},
        "total": sum(len(found) for found in per_file.values()),
        "index": {
            compact(title): name
            for name, found in per_file.items()
            for _level, title in found
        },
    }


# The five contents entries that match no heading, each read against the source.
DISPOSITIONS = {
    "Legal Information": (
        "Owned by the controlled addition legal-information.md, which is not "
        "one of the thirteen upstream content files. Official page 1."
    ),
    "Dropping to": (
        "An artifact of reading the contents: the entry is 'Dropping to 0 Hit "
        "Points 17' and the split above takes its inner number as the page. "
        "The heading is playing-the-game.md 'Dropping to 0 Hit Points'."
    ),
    "Running a Monster": (
        "Present in monsters.md as the sidebar '> **Running a Monster**' "
        "rather than a Markdown heading. Official page 255 is quiet in the "
        "token pass."
    ),
    "Index of Stat Blocks Aboleth": (
        "Two contents entries the split above merged, because the section "
        "label carries no dot leader. 'Index of Stat Blocks' is navigation; "
        "the index itself begins at the Aboleth heading monsters-A-Z.md owns. "
        "Official page 258 is quiet in the token pass."
    ),
    "Warrior Veteran": (
        "OWNER CORRECTION, not publisher text: the stat block the contents and "
        "official page 337 name 'Warrior Veteran' is headed 'Veteran Warrior' "
        "in monsters-A-Z.md, the name Deck of Illusions prints for it. Same "
        "stat block; recorded in source_pin.json under Monsters A-Z > "
        "Warriors > Warrior Veteran."
    ),
}


def table_of_contents(pages: dict[int, object], index: dict[str, str]) -> dict:
    """Official pp.2-4 enumerate the document; check the source owns each entry.

    The comparison skips the front matter, so the contents pages are the one
    part of the official document no page-by-page check covers, and they are an
    enumeration of what the document contains.

    What this establishes is narrow and worth stating: for each contents entry,
    some heading somewhere in the snapshot carries that title. It does not say
    the heading is at the right depth, that it owns the right material, or that
    the titles it does not list are placed correctly — the contents list
    sections, not the thousands of entries beneath them. Ownership is read by
    :func:`record_ownership` instead.
    """
    text = re.sub(r"\s+", " ", " ".join(cc.page_text(pages[n]) for n in (2, 3, 4)))  # type: ignore[arg-type]
    chunks = re.split(r"\.{2,}", text)
    entries: list[tuple[str, int]] = []
    title = chunks[0].removeprefix("Contents").strip()
    for chunk in chunks[1:]:
        match = re.match(r"\s*(\d{1,3})\s*(.*)$", chunk)
        assert match, repr(chunk[:60])
        entries.append((title, int(match.group(1))))
        title = match.group(2).strip()
        # A few entries are set without a dot leader, so their page number sits
        # inside the next title. Take the trailing number as that entry's page.
        inner = re.match(r"^(.*?[a-z]) (\d{1,3}) (.*)$", title)
        if inner:
            entries.append((inner.group(1), int(inner.group(2))))
            title = inner.group(3).strip()
    if title:
        entries.append((title, 0))
    missing = [
        {"title": t, "official_page": p, "disposition": DISPOSITIONS[t]}
        for t, p in entries
        if compact(t) not in index
    ]
    return {
        "establishes": (
            "every contents entry is the title of some heading in the snapshot"
        ),
        "does_not_establish": (
            "the depth of that heading, what it owns, or the placement of the "
            "headings the contents does not list"
        ),
        "entries": len(entries),
        "entries_whose_title_matches_a_heading": len(entries) - len(missing),
        "entries_without_a_heading": missing,
    }


def main() -> int:
    pages = extract_pages(ROOT / cc.PDF_REPO_PATH)
    by_page = {p.printed_page: p for p in pages}
    raw = {
        name: (ROOT / cc.PIN_DIR / name).read_text(encoding="utf-8")
        for name in cc.CONTENT_FILES
    }
    manifest = json.loads(
        (ROOT / cc.PIN_DIR / "source_pin.json").read_text(encoding="utf-8")
    )

    record = cc.compare(
        pages, cc.community_text(ROOT), pin_commit=str(manifest["upstream_commit"])
    )

    inventory = ct.inventory(pages, raw)
    body = [row for row in inventory if row.printed_page not in cc.FRONT_MATTER]
    order = {row.printed_page: row for row in ct.number_order(pages, raw)}

    snapshot_chars = {
        name: len(ct.normalized(cc.markdown_text(text)).compact)
        for name, text in raw.items()
    }
    covered: Counter[str] = Counter()
    for row in inventory:
        for name, lo, hi in row.spans:
            covered[name] += hi - lo + 1

    head = headings(raw)
    index = head.pop("index")
    assert isinstance(index, dict)

    over_floor = record["discrepancies"]["runs"]  # type: ignore[index]
    noisy = {row.printed_page for row in inventory if not row.quiet}

    record["qualification"] = {
        "generated_by": COMMAND,
        "what_this_adds": (
            "The window pass above compares characters after compaction and "
            "says so: signs, cell association and record ownership are outside "
            "it. Each has its own pass here, so that no figure rests on a "
            "coverage percentage alone. Signs and cell association are read by "
            "the token pass and the structure scan; record ownership is read "
            "by the ownership pass, which is the one thing a comparison of "
            "text cannot see at all, because a heading mark is not text the "
            "official page prints."
        ),
        "scope": {
            "full_mechanical_scans": {
                "token_pass": "all 364 official pages against the whole snapshot",
                "number_order_pass": "all 360 body pages",
                "structure": "every table, ability grid and arithmetic triple",
                "record_ownership": "every heading in the thirteen content files",
                "snapshot_is_partitioned_without_gaps": "every snapshot character",
            },
            "representative_reads": {
                "official_table_of_contents": (
                    "481 contents entries, checked for title presence only"
                ),
                "pages_rendered_and_read_directly": (
                    "the residue and correction pages named in the corrections "
                    "notes, not all 364"
                ),
                "why_separated": (
                    "A scan's count is a count of everything there is. A read's "
                    "count is a count of what was looked at. Reported together, "
                    "the first would stand in for the second."
                ),
            },
        },
        "token_pass": {
            "module": ct.__name__,
            "comparison": (
                "per-official-page token multisets, minus sign preserved, "
                "order-immune"
            ),
            "body_pages": len(body),
            "quiet_body_pages": sum(1 for row in body if row.quiet),
            "pdf_only_tokens_outside_front_matter": sum(
                sum(row.pdf_only.values()) for row in body
            ),
            "snapshot_only_tokens_outside_front_matter": sum(
                sum(row.snapshot_only.values()) for row in body
            ),
            "pages_with_residue": [
                {
                    "printed_page": row.printed_page,
                    "files": list(row.files),
                    "pdf_only": dict(row.pdf_only),
                    "snapshot_only": dict(row.snapshot_only),
                }
                for row in body
                if not row.quiet
            ],
        },
        "snapshot_is_partitioned_without_gaps": {
            "why": (
                "Every character of the snapshot is assigned to exactly one "
                "official page, so a window-pass run that could not be anchored "
                "is an alignment limit of that pass, not unexamined content."
            ),
            "compact_chars": sum(snapshot_chars.values()),
            "chars_assigned_to_a_page": sum(covered.values()),
        },
        "number_order_pass": {
            "why": (
                "A multiset cancels a difference that stays on one page. Read "
                "in order, a dropped table row and a swapped pair of cells do "
                "not cancel. Pages whose sequences differ were read; a page "
                "printed in two columns legitimately differs."
            ),
            "body_pages": len(body),
            "pages_with_the_same_number_order": sum(
                1 for row in body if order[row.printed_page].same_order
            ),
            "each_differing_page_was_read": (
                "The families are recorded in the corrections notes. Four are "
                "not page-column reading order. Official pp.101-102 set the "
                "Food, Drink, and Lodging list in paired sub-columns that the "
                "extraction reads across, while the corrected file carries the "
                "list in the order the pages print it (correction family I). "
                "The Staff of the Magi table on official "
                "pages 246-247 had lost a row under the header the document "
                "reprints at the page break. Official p.222 differs because "
                "the Giant Fly stat block was moved to the end of the "
                "Figurine of Wondrous Power entry, so its numbers now follow "
                "the figurine variants the official page prints past it "
                "rather than preceding them. Official p.340 prints the Young "
                "White Dragon's INT save as '2'; the snapshot carries the "
                "official-source-backed '-2' (correction family N)."
            ),
            "pages_read_because_their_number_order_differs": sorted(
                row.printed_page
                for row in body
                if not order[row.printed_page].same_order
            ),
        },
        "official_table_of_contents": table_of_contents(by_page, index),  # type: ignore[arg-type]
        "headings": head,
        "record_ownership": record_ownership(raw),
        "structure": structure(raw),
        "window_pass_runs_over_floor": {
            "total": len(over_floor),  # type: ignore[arg-type]
            "on_a_page_the_token_pass_also_reports": sum(
                1 for run in over_floor if run["printed_page"] in noisy  # type: ignore[index]
            ),
            "front_matter": sum(
                1 for run in over_floor if run["front_matter"]  # type: ignore[index]
            ),
            "note": (
                "A run on a page the token pass reports quiet holds the same "
                "tokens with the same multiplicities in the same page, so it is "
                "a reading-order difference, not missing or altered content."
            ),
        },
        "corrections": {
            "applied": manifest["corrections_applied"],
            "files": {
                str(entry["path"]): len(entry["corrections"])  # type: ignore[arg-type]
                for entry in manifest["files"]
                if entry["corrections"]
            },
            "preserved_official_defects": manifest["preserved_official_defects"],
            "controlled_additions": [
                {k: v for k, v in add.items() if k != "sha256"}
                for add in manifest["controlled_additions"]
            ],
            "notes": "docs/architecture/issue-5c-5d-community-source-corrections.md",
        },
        "remaining": [
            "Qualification is of the source and is complete when the source's "
            "own defects are resolved and the evidence has been reviewed "
            "independently. A later consumer reading these bytes is a "
            "different question and cannot be what qualifies them; a corpus "
            "built from this source is qualified separately, on its own "
            "evidence.",
            "legal-information.md is a controlled addition and is not one of "
            "the thirteen content files the comparison covers, because it has "
            "no upstream counterpart. Ingestion must pick it up separately so "
            "the attribution travels with the corpus.",
            "No difference is preserved as an official defect. The official "
            "page prints the Young White Dragon's INT save on p.340 unsigned, "
            "as does the Basic Rules rendering; the current official "
            "individual stat block prints it -2. The snapshot follows the "
            "individual stat block (correction family N, an official-source "
            "disagreement recorded as a correction, not an Owner decision and "
            "not a formal erratum), so preserved_official_defects is empty.",
            "Two places where the official document itself reads oddly were "
            "rendered from the PDF and read directly, by this work and again "
            "independently: the Telekinesis sentence truncated mid-clause at "
            "the foot of p.168, and the unsigned INT save on p.340. The PDF "
            "prints the first as the snapshot now holds it; the second is now "
            "corrected on official-source evidence (see above), and the PDF "
            "page stays the evidence of what it prints. Both stand here as "
            "anomaly notes about the official text. Neither says anything "
            "about how a later runtime should read them, and neither is a "
            "judgement that the content is correct. The Telekinesis wording "
            "removed is quoted verbatim in the manifest and reverses in one "
            "step.",
        ],
    }

    OUT.write_text(
        json.dumps(record, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    qualification = record["qualification"]
    assert isinstance(qualification, dict)
    print(OUT)
    for key in ("token_pass", "number_order_pass", "structure"):
        print(key, json.dumps(qualification[key])[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
