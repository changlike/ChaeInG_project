from app.services.ingredient_parser import (
    clean_source_url,
    extract_amount,
    normalize_name,
    parse_ingredients,
    review_reason,
    split_ingredients,
)


def test_split_basic():
    assert split_ingredients("정제수, 글리세린, 부틸렌글라이콜") == ["정제수", "글리세린", "부틸렌글라이콜"]


def test_split_keeps_comma_between_digits():
    assert split_ingredients("정제수, 1,2-헥산다이올, 글리세린") == ["정제수", "1,2-헥산다이올", "글리세린"]


def test_split_keeps_comma_inside_parentheses():
    assert split_ingredients("정제수, 하이알루로닉애씨드(1,000ppm), 글리세린") == [
        "정제수",
        "하이알루로닉애씨드(1,000ppm)",
        "글리세린",
    ]


def test_split_space_separated_list():
    assert split_ingredients("정제수 글리세린 부틸렌글라이콜") == ["정제수", "글리세린", "부틸렌글라이콜"]


def test_split_ignores_empty_parts_and_extra_spaces():
    assert split_ingredients("정제수,  ,  글리세린 ,") == ["정제수", "글리세린"]


def test_extract_amount():
    assert extract_amount("나이아신아마이드(2%)") == ("나이아신아마이드", "2%")
    assert extract_amount("하이알루로닉애씨드(1,000ppm)") == ("하이알루로닉애씨드", "1,000ppm")
    assert extract_amount("정제수") == ("정제수", None)


def test_extract_amount_does_not_empty_the_name():
    assert extract_amount("(2%)") == ("(2%)", None)


def test_parse_ingredients_positions_and_amounts():
    result = parse_ingredients("정제수, 나이아신아마이드(2%), 글리세린")
    assert result == [
        {"position": 1, "name": "정제수", "amount_note": None},
        {"position": 2, "name": "나이아신아마이드", "amount_note": "2%"},
        {"position": 3, "name": "글리세린", "amount_note": None},
    ]


def test_parse_ingredients_removes_asterisk_and_duplicates():
    result = parse_ingredients("정제수, *알로에베라잎추출물, 알로에베라잎추출물, 글리세린")
    assert [r["name"] for r in result] == ["정제수", "알로에베라잎추출물", "글리세린"]
    assert [r["position"] for r in result] == [1, 2, 3]


def test_extract_amount_without_parentheses():
    assert extract_amount("판테놀 50,000ppm") == ("판테놀", "50,000ppm")


def test_extract_amount_ignores_percent_after_comma_inside_parentheses():
    assert extract_amount("징크피씨에이(징크로서,1%)") == ("징크피씨에이(징크로서,1%)", None)


def test_normalize_name_removes_spaces():
    assert normalize_name("소듐하이알루로 네이트", aliases={}) == "소듐하이알루로네이트"


def test_normalize_name_applies_alias_and_drop():
    aliases = {"향료료": "향료", "아벤느": ""}
    assert normalize_name("향료료", aliases) == "향료"
    assert normalize_name("아벤느", aliases) == ""


def test_parse_ingredients_normalizes_and_drops_empty_alias():
    result = parse_ingredients("정제수, 소듐하이 알루로네이트, 아벤느, 향료료", aliases={"아벤느": "", "향료료": "향료"})
    assert [r["name"] for r in result] == ["정제수", "소듐하이알루로네이트", "향료"]


def test_parse_ingredients_splits_set_markers_and_label():
    result = parse_ingredients("전성분 정제수, 글리세린 (2제) 정제수, 판테놀", aliases={})
    assert [r["name"] for r in result] == ["정제수", "글리세린", "판테놀"]


def test_parse_ingredients_splits_items_merged_after_parentheses():
    result = parse_ingredients("정제수, 하이드롤라이즈드하이알루로닉애씨드(0.1ppm) 소듐하이알루로네이트", aliases={})
    assert [r["name"] for r in result] == ["정제수", "하이드롤라이즈드하이알루로닉애씨드", "소듐하이알루로네이트"]
    assert result[1]["amount_note"] == "0.1ppm"


def test_review_reason():
    assert review_reason("정제수, 글리세린") is None
    assert review_reason("[세럼] 정제수, [크림] 글리세린") is not None
    assert review_reason("정제수, *레티놀 복합체: 설명") is not None


def test_clean_source_url_keeps_only_goods_no():
    url = "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000123&trackingCd=abc"
    assert clean_source_url(url) == "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000123"


def test_clean_source_url_without_goods_no_returns_original():
    assert clean_source_url("  https://example.com/page  ") == "https://example.com/page"
