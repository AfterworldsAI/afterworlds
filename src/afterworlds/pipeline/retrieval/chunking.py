"""Chunking policy for story-memory ingestion — CRD Issue 18 / ADR-018 D3.

One chunk per delivered turn's prose under a configured character ceiling;
above it, split on paragraph boundaries. No semantic chunker, no overlap
windows in v1.
"""

from __future__ import annotations


def chunk_turn_prose(text: str, ceiling: int) -> list[str]:
    """Split *text* into chunks of at most *ceiling* characters.

    Splits on paragraph boundaries (blank-line-separated) when the full text
    exceeds the ceiling. A single paragraph longer than the ceiling is kept
    whole as its own chunk (no mid-paragraph splitting in v1) rather than
    silently truncated. Returns ``[text]`` unchanged when it already fits.
    """
    if not text:
        return [text]
    if len(text) <= ceiling:
        return [text]

    paragraphs = [p for p in text.split("\n\n") if p]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= ceiling:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = paragraph
    if current:
        chunks.append(current)
    return chunks or [text]
