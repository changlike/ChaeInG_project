from app.core.search import escape_like


def test_percent_is_escaped():
    assert escape_like("%") == "\\%"


def test_underscore_is_escaped():
    assert escape_like("a_b") == "a\\_b"


def test_backslash_is_escaped_first():
    assert escape_like("\\%") == "\\\\\\%"


def test_plain_text_unchanged():
    assert escape_like("토너") == "토너"
