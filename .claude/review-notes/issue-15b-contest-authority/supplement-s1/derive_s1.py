"""Derive candidate S1 (CRD Issue 15b): the Owner-adopted SRD 5.1 contest
supplement as one authored ``package_patch`` override. REVIEW MATERIAL ONLY:
nothing is accepted, authored into a store, published or activated. Run from
the repository root with the worktree venv (``pypdf`` is a review-tool
dependency, not a project one):

    PYTHONIOENCODING=utf-8 venv/Scripts/python.exe \
        .claude/review-notes/issue-15b-contest-authority/supplement-s1/derive_s1.py \
        [--pdf PATH]

Reads the pinned official SRD 5.1 PDF (default: the Codex scratch copy), the
Owner policy receipt and the reviewed proposal, each digest-checked. Writes
``page-77-extract.txt`` (the raw page text) and ``s1.json`` (the candidate).
Byte-identical across runs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import uuid
from pathlib import Path

REPO = Path.cwd()
HERE = REPO / ".claude/review-notes/issue-15b-contest-authority/supplement-s1"
SCRATCH = Path("D:/AI/Claude/scratch/AW docs/issue15b-resumption")
PDF_SHA256 = "2504d2a0abb0a4d491a939be4f17910a2dde0312570ab8d208080225ccf0a1f0"  # pragma: allowlist secret
PDF_BYTES = 3158713
PDF_URL = "https://media.dndbeyond.com/compendium-images/srd/5.1/SRD_CC_v5.1.pdf"
PAGE_INDEX = 76  # printed page 77
LEGAL_PAGE_INDEX = 0
RECEIPT = SCRATCH / "CONTEST-SUPPLEMENT-OWNER-ACCEPTANCE-2026-10-14.md"
RECEIPT_SHA256 = None  # recorded, not pre-pinned: the receipt is Codex's file
PROPOSAL = SCRATCH / "PROPOSED-OPPOSED-CHECK-CONTRACT.md"
PROPOSAL_SHA256 = "6e708e77dcbe3fefcd3d0cef7aaf9fdff2c3ee783b9e3d3df3b8f01a3d338a20"  # pragma: allowlist secret

RELEASE = ("1299484e-c72d-509b-bd8d-d0169ee1f8d2", "5.2.1-corpus.8781d4e0-a3b")
SUPPLEMENT_ID = "afterworlds.supplement.srd-5-1-contests"
SUPPLEMENT_VERSION = 1
#: Deterministic, so the supplement component's schema identity (and any
#: future contest fingerprint) is computable before anything is authored.
OVERRIDE_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"afterworlds:{SUPPLEMENT_ID}:v1"))

#: Every whitespace run pypdf emits between words (tab, CR, LF, NBSP, space).
WHITESPACE = re.compile(r"[\t\r\n\xa0 ]+")
#: Words the PDF's text layer splits with a stray space. Each is asserted to
#: occur exactly once in the excerpt and is listed in the candidate; nothing
#: else is changed. Typographic apostrophes (U+2019) and the dash (U+2014)
#: are extracted as-is and kept.
CORRECTIONS = (("e fforts", "efforts"), ("th e action", "the action"), ("of f", "off"))
START = "Sometimes one character’s or monster’s efforts"
END = "a tie means that the door remains shut."

#: The three points the Owner accepted, verbatim from the receipt.
POLICY_POINTS = (
    "Code compares the participants' authoritative final check totals; the "
    "greater total wins.",
    "Equal totals preserve the situation that existed before the contest. No "
    "automatic reroll or universal acting-side win is implied.",
    "Applicable specific SRD 5.2.1 mechanics remain unchanged unless separately "
    "overridden. Hide's recorded-result DC, Influence's formula DC and "
    "Grapple/Shove's saving throws are not silently converted into generic "
    "contests.",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def page_text(pdf: Path, index: int) -> str:
    import pypdf  # review-tool dependency only

    return pypdf.PdfReader(str(pdf)).pages[index].extract_text()


def excerpt_from(raw: str) -> tuple[str, list[dict[str, object]]]:
    flat = WHITESPACE.sub(" ", raw)
    start = flat.index("Contests Sometimes") + len("Contests ")
    end = flat.index(END, start) + len(END)
    assert flat[end:].lstrip().startswith("Skills Each ability"), flat[end : end + 40]
    text = flat[start:end]
    applied = []
    for wrong, right in CORRECTIONS:
        assert text.count(wrong) == 1, (wrong, text.count(wrong))
        at = text.index(wrong)
        text = text.replace(wrong, right)
        applied.append({"extracted": wrong, "corrected": right, "offset": at})
    assert text.startswith(START) and text.endswith(END), text[:80]
    return text, applied


def attribution_from(raw: str) -> str:
    flat = WHITESPACE.sub(" ", raw)
    start = flat.index("This work includes material taken from")
    end = flat.index("legalcode.", start) + len("legalcode.")
    return flat[start:end]


def authored_prose(excerpt: str, attribution: str) -> str:
    points = "\n".join(f"{n}. {p}" for n, p in enumerate(POLICY_POINTS, 1))
    return (
        f"Afterworlds supplement {SUPPLEMENT_ID}, version {SUPPLEMENT_VERSION}: "
        "generic two-participant ability-check contests. Adopted by the Owner on "
        "14 October 2026 as an explicit supplement to this SRD 5.2.1 release; it "
        "is not SRD 5.2.1 content. Only the contest procedure below is adopted; "
        "System Reference Document 5.1 is not otherwise imported.\n\n"
        'Source: System Reference Document 5.1, "Contests", printed page 77:\n'
        f"{excerpt}\n\n"
        f"Application in this package:\n{points}\n\n"
        f"{attribution}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=SCRATCH / "SRD_CC_v5.1-contest-source.pdf")
    args = parser.parse_args()
    pdf_bytes = args.pdf.read_bytes()
    assert len(pdf_bytes) == PDF_BYTES and sha(pdf_bytes) == PDF_SHA256, args.pdf
    assert sha(PROPOSAL.read_bytes()) == PROPOSAL_SHA256
    receipt = RECEIPT.read_text("utf-8")
    for point in POLICY_POINTS:
        assert point in receipt, point

    raw = page_text(args.pdf, PAGE_INDEX)
    (HERE / "page-77-extract.txt").write_bytes(raw.encode("utf-8"))
    excerpt, applied = excerpt_from(raw)
    attribution = attribution_from(page_text(args.pdf, LEGAL_PAGE_INDEX))
    prose = authored_prose(excerpt, attribution)

    payload = {
        "patch": "append_component",
        "component": {
            "semantic_key": "contest",
            "handling": "prose_bound",
            "facts": [],
            "authored_prose": prose,
        },
    }
    candidate = {
        "candidate_id": "15b-S1-contest-supplement",
        "status": "CANDIDATE: not accepted, authored, published or activated",
        "supplement_id": SUPPLEMENT_ID,
        "supplement_version": SUPPLEMENT_VERSION,
        "source": {
            "title": "System Reference Document 5.1 (Creative Commons edition)",
            "url": PDF_URL,
            "sha256": PDF_SHA256,
            "bytes": PDF_BYTES,
            "section": "Contests",
            "printed_page": 77,
            "pdf_page_index": PAGE_INDEX,
            "license": "CC-BY-4.0",
            "page_extract_sha256": sha(raw.encode("utf-8")),
        },
        "owner_policy": {
            "receipt": RECEIPT.name,
            "receipt_sha256": sha(RECEIPT.read_bytes()),
            "proposal": PROPOSAL.name,
            "proposal_sha256": PROPOSAL_SHA256,
            "points": list(POLICY_POINTS),
        },
        "excerpt": {
            "text": excerpt,
            "normalization": "every run of tab, CR, LF, NBSP or space -> one space",
            "corrections": applied,
        },
        "attribution": attribution,
        "override": {
            "override_id": OVERRIDE_ID,
            "release_version": RELEASE[1],
            "package_uuid": RELEASE[0],
            "origin": "package_patch",
            "operation": "append",
            "target": {"kind": "record", "record_key": "play.d20_tests"},
            "precedence": 0,
            "is_enabled": True,
            "payload": payload,
        },
        "authored_prose_sha256": sha(prose.encode("utf-8")),
    }
    out = json.dumps(candidate, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    (HERE / "s1.json").write_bytes(out.encode("utf-8"))
    print(f"s1.json {sha(out.encode('utf-8'))}")
    print(f"override_id {OVERRIDE_ID}")


if __name__ == "__main__":
    main()
