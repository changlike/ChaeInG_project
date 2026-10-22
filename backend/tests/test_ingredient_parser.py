from app.services.ingredient_parser import (
    clean_source_url,
    extract_amount,
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


def test_review_reason():
    assert review_reason("정제수, 글리세린") is None
    assert review_reason("[세럼] 정제수, [크림] 글리세린") is not None
    assert review_reason("정제수, *레티놀 복합체: 설명") is not None


def test_clean_source_url_keeps_only_goods_no():
    url = "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000123&trackingCd=abc"
    assert clean_source_url(url) == "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000123"


def test_clean_source_url_without_goods_no_returns_original():
    assert clean_source_url("  https://example.com/page  ") == "https://example.com/page"
