from app.formatting import escape_markdown_v2, chunk_text


def test_escape_markdown_v2():
    s = "Hello_[World]! (test) #1"
    out = escape_markdown_v2(s)
    assert out == "Hello\\_\\[World\\]\\! \\(" "test" "\\) \\#1"


def test_chunk_text():
    text = "a" * 10
    chunks = chunk_text(text, 4)
    assert chunks == ["aaaa", "aaaa", "aa"]


