from scripts.apply_concerns import build_updates, parse_concerns


def row(url, draft, verified="", reviewed=""):
    return {"product_name": url, "source_url": url, "draft_concerns": draft,
            "verified_concerns": verified, "reviewed": reviewed}


def test_only_reviewed_rows_by_default():
    rows = [row("a", "건조/보습"), row("b", "모공", reviewed="o")]
    updates, errors = build_updates(rows)
    assert errors == []
    assert updates == [{"source_url": "b", "main_concerns": ["모공"], "verified": True}]


def test_verified_value_overrides_draft():
    updates, _ = build_updates([row("a", "건조/보습,홍조", verified="홍조", reviewed="o")])
    assert updates[0]["main_concerns"] == ["홍조"]


def test_with_drafts_marks_unverified():
    updates, _ = build_updates([row("a", "건조/보습")], with_drafts=True)
    assert updates == [{"source_url": "a", "main_concerns": ["건조/보습"], "verified": False}]


def test_invalid_vocab_is_error():
    updates, errors = build_updates([row("a", "", verified="보습", reviewed="o")])
    assert updates == [] and len(errors) == 1


def test_no_concern_keyword():
    assert parse_concerns("없음") == []
