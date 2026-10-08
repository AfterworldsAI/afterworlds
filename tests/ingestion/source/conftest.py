"""One extraction of the official PDF, shared by every test in this package.

Extracting all 364 pages takes about half a minute, so a module-scoped fixture
per test file pays that cost once per file. The comparison and the token pass
both need the same pages and neither mutates them — :class:`ExtractedPage` is
frozen — so they share one session-scoped extraction.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from afterworlds.ingestion.corpus.pdf_source import ExtractedPage, extract_pages
from afterworlds.ingestion.source import community_compare as cc

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def official_pages() -> list[ExtractedPage]:
    """Every page of the authoritative PDF, in reading order."""
    return extract_pages(REPO_ROOT / cc.PDF_REPO_PATH)
