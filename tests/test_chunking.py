import pytest

from web_summarizer.chunking import chunk_text


def test_short_text_remains_one_chunk():
    assert chunk_text("one two three", max_words=10, overlap_words=2) == [
        "one two three"
    ]


def test_long_text_is_split_with_bounded_chunks_and_overlap():
    words = [f"word-{index}" for index in range(25)]
    chunks = chunk_text(
        " ".join(words),
        max_words=10,
        overlap_words=2,
    )

    assert len(chunks) == 3
    assert all(len(chunk.split()) <= 10 for chunk in chunks)
    assert chunks[0].split()[-2:] == chunks[1].split()[:2]
    assert chunks[1].split()[-2:] == chunks[2].split()[:2]


def test_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text("text", max_words=10, overlap_words=10)

