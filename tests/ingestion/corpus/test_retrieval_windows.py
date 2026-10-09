"""Every embedding document the real corpus produces fits the model's ceiling.

The defect this file exists for: the local ONNX MiniLM embedding function calls
``tokenizer.enable_truncation(max_length=256)`` on its own input, so a chunk sent
whole was embedded from its opening alone while the stored document still read
back complete. Nothing in the vector-state verification could see it -- the
document hashes match either way -- so the only honest check is to encode what
is actually sent with the model's own tokenizer and measure.

That is what this module does, over the whole replacement corpus, through the
same ``derive_retrieval_documents`` the reindex writer calls. It reads the
cached tokenizer directly and touches no Chroma store and no database.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from afterworlds.ingestion.corpus.pipeline import CandidateRelease
from afterworlds.pipeline.retrieval.corpus_windows import (
    WINDOW_CHAR_BUDGET,
    derive_windows,
    visible_text,
)

#: Chroma's cached MiniLM tokenizer, written by its first real embed. The
#: truncation ceiling lives in the same directory's model config.
TOKENIZER_PATH = (
    Path.home() / ".cache/chroma/onnx_models/all-MiniLM-L6-v2/onnx/tokenizer.json"
)

#: ``onnx_mini_lm_l6_v2.py``'s own ``enable_truncation(max_length=256)``.
EMBEDDING_TOKEN_CEILING = 256


@pytest.fixture(scope="module")
def tokenizer():  # type: ignore[no-untyped-def]
    """The model's own tokenizer, with the runtime limits removed.

    Truncation and padding are disabled deliberately: the file configures both
    at 128, and Chroma overrides them to 256 at embed time. Measuring a *capped*
    encoder would report 256 for an input of any length, which is exactly the
    blindness this test exists to remove.
    """
    if not TOKENIZER_PATH.exists():
        pytest.skip(f"MiniLM tokenizer not cached at {TOKENIZER_PATH}")
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(str(TOKENIZER_PATH))
    tok.no_truncation()
    tok.no_padding()
    return tok


def test_whole_text_of_the_real_corpus_would_have_been_truncated(
    source_candidate: CandidateRelease, tokenizer
) -> None:
    """The defect, measured on the corpus that ships -- not a constructed case.

    This asserts the *old* behavior was broken, so the fix below is not proving
    something that was never a problem.
    """
    oversized = [
        chunk
        for chunk in source_candidate.members.chunks
        if len(tokenizer.encode(chunk.content).ids) > EMBEDDING_TOKEN_CEILING
    ]
    assert len(oversized) > 400, len(oversized)


def test_every_derived_window_of_the_real_corpus_fits_the_ceiling(
    source_candidate: CandidateRelease, tokenizer
) -> None:
    """The guarantee. No window of any chunk reaches the truncation ceiling.

    Measured through the model's own tokenizer on the text actually sent, with
    a recorded margin: ``WINDOW_CHAR_BUDGET`` is a character count and this is
    what makes it a token guarantee for this corpus.
    """
    worst = 0
    total = 0
    for chunk in source_candidate.members.chunks:
        for window in derive_windows(chunk.content, chunk.section_label):
            total += 1
            worst = max(worst, len(tokenizer.encode(window.text).ids))
    assert total >= len(source_candidate.members.chunks)
    assert worst <= EMBEDDING_TOKEN_CEILING, worst
    # A real margin, not a coincidence one source edit away from the ceiling.
    assert worst <= EMBEDDING_TOKEN_CEILING - 32, worst


def test_windowing_adds_few_documents_and_leaves_short_chunks_whole(
    source_candidate: CandidateRelease,
) -> None:
    """Windowing is for the chunks that need it, not a corpus-wide reshaping."""
    chunks = source_candidate.members.chunks
    counts = [
        len(derive_windows(chunk.content, chunk.section_label)) for chunk in chunks
    ]
    assert all(count >= 1 for count in counts)
    # The great majority of units are one window; the split is the exception.
    assert sum(1 for count in counts if count > 1) < len(chunks) // 10
    assert sum(counts) < len(chunks) * 2


def test_every_window_carries_its_section_label_and_the_content_is_complete(
    source_candidate: CandidateRelease,
) -> None:
    """Nothing is dropped, and a window from the middle still says where it is.

    Completeness is checked as a set of words rather than a substring: the
    derived text deliberately replaces markup with whitespace, so the visible
    words are what must survive, not the byte sequence.
    """
    for chunk in source_candidate.members.chunks:
        windows = derive_windows(chunk.content, chunk.section_label)
        label = (chunk.section_label or "").strip()
        if label:
            assert all(w.text.startswith(label) for w in windows)
        expected = visible_text(chunk.content).split()
        recovered = [
            word for w in windows for word in w.text[len(label) :].split()  # noqa: E203
        ]
        assert recovered == expected, chunk.chunk_id


def test_the_magic_item_rarity_note_travels_with_its_table(
    source_candidate: CandidateRelease,
) -> None:
    """R1 and R2 together: the note is in the unit, and it reaches a window.

    A consumer that retrieves any window of the rarities table can still be
    served the note, because hydration returns the whole unit -- but the note
    must also be *findable*, which requires it to be embedded somewhere.
    """
    matches = [
        chunk
        for chunk in source_candidate.members.chunks
        if "Magic Item Rarities and Values" in chunk.content
        and "<table>" in chunk.content
    ]
    assert len(matches) == 1
    assert matches[0].source_locator_value == "p. 206"
    chunk = matches[0]
    assert "Halve the value for a consumable item" in chunk.content
    windows = derive_windows(chunk.content, chunk.section_label)
    assert any("Halve the value for a consumable item" in w.text for w in windows)


def test_a_chunk_with_no_section_label_still_produces_bounded_windows() -> None:
    """Custom Rules Packages may have a null label; the budget still applies."""
    content = " ".join(f"word{index}" for index in range(500))
    windows = derive_windows(content, None)
    assert len(windows) > 1
    assert all(len(w.text) <= WINDOW_CHAR_BUDGET for w in windows)
    assert [w.count for w in windows] == [len(windows)] * len(windows)
    assert [w.index for w in windows] == list(range(len(windows)))
    assert " ".join(w.text for w in windows).split() == content.split()
