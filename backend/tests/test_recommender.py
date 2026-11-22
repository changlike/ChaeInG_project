from app.services.recommender import (
    recommend, check_gates, find_warnings, find_trace_warnings, split_ingredient_text,
    REASON_SENSITIVE, REASON_BANNED, REASON_AVOIDED, MATCH_MAIN, MATCH_CONTAINED, MATCH_NONE,
)

IRRITANTS = [
    {"ingredient_name": "향료", "position_rule": "any", "reason": "향료"},
    {"ingredient_name": "에탄올", "position_rule": "top_n", "reason": "알코올(에탄올)"},
]
REGULATED = [
    {"ingredient_name": "금지성분", "regulate_type": "금지", "limit_cond": ""},
    {"ingredient_name": "페녹시에탄올", "regulate_type": "한도", "limit_cond": "1%"},
]


def make_product(pid, concerns, names, verified=True):
    return {
        "id": pid,
        "product_name": f"제품{pid}",
        "brand": "브랜드",
        "category": "크림",
        "main_concerns": concerns,
        "is_concerns_verified": verified,
        "ingredients": [{"name": n, "position": i} for i, n in enumerate(names, start=1)],
    }


def profile(**kw):
    base = {"is_sensitive": False, "concerns": [], "avoided_ingredients": None, "preferred_ingredients": None}
    return {**base, **kw}


# --- 1단계 게이트 ---

def test_sensitive_user_drops_irritant_product():
    p = make_product(1, [], ["정제수", "향료"])
    reasons = check_gates(p, profile(is_sensitive=True), IRRITANTS, [])
    assert [r["type"] for r in reasons] == [REASON_SENSITIVE]


def test_non_sensitive_user_keeps_irritant_product():
    p = make_product(1, [], ["정제수", "향료"])
    assert check_gates(p, profile(is_sensitive=False), IRRITANTS, []) == []


def test_top_n_irritant_gates_only_in_front_of_boundary():
    # 경계 = 처음 나오는 소량 성분(마커) 바로 앞. 알코올류는 경계 앞이면 탈락, 뒤(소량)면 탈락시키지 않음
    markers = ["페녹시에탄올"]
    front = make_product(1, [], ["정제수", "에탄올", "페녹시에탄올"])
    back = make_product(2, [], ["정제수", "페녹시에탄올", "에탄올"])
    assert check_gates(front, profile(is_sensitive=True), IRRITANTS, [], markers)
    assert check_gates(back, profile(is_sensitive=True), IRRITANTS, [], markers) == []


def test_any_irritant_gates_regardless_of_boundary():
    markers = ["페녹시에탄올"]
    p = make_product(1, [], ["정제수", "페녹시에탄올", "향료"])
    assert check_gates(p, profile(is_sensitive=True), IRRITANTS, [], markers)


def test_trace_irritant_is_warning_for_sensitive_user_only():
    markers = ["페녹시에탄올"]
    back = make_product(1, [], ["정제수", "페녹시에탄올", "에탄올"])
    warnings = find_trace_warnings(back, profile(is_sensitive=True), IRRITANTS, markers)
    assert [w["ingredient"] for w in warnings] == ["에탄올"] and warnings[0]["kind"] == "trace_irritant"
    assert find_trace_warnings(back, profile(is_sensitive=False), IRRITANTS, markers) == []


def test_banned_ingredient_drops_for_everyone():
    p = make_product(1, [], ["정제수", "금지성분"])
    reasons = check_gates(p, profile(), [], REGULATED)
    assert [r["type"] for r in reasons] == [REASON_BANNED]


def test_avoided_keyword_matches_substring():
    p = make_product(1, [], ["정제수", "변성알코올"])
    reasons = check_gates(p, profile(avoided_ingredients="알코올"), [], [])
    assert reasons == [{"type": REASON_AVOIDED, "ingredient": "변성알코올", "detail": "기피 성분 '알코올'"}]


def test_split_ingredient_text_ignores_blank_and_spaces():
    assert split_ingredient_text(" 나이아신 아마이드, ,히알루론산 ") == ["나이아신아마이드", "히알루론산"]
    assert split_ingredient_text(None) == []


# --- 3단계 경고 ---

def test_limited_ingredient_is_warning_not_gate():
    p = make_product(1, ["건조/보습"], ["정제수", "페녹시에탄올"])
    assert check_gates(p, profile(), [], REGULATED) == []
    assert find_warnings(p, REGULATED) == [{"ingredient": "페녹시에탄올", "limit_cond": "1%", "kind": "limit"}]


# --- 2단계 가산점 + 전체 흐름 ---

def test_sorted_by_match_count_not_sum():
    products = [
        make_product(1, ["건조/보습"], ["정제수"]),
        make_product(2, ["건조/보습", "모공"], ["정제수"]),
        make_product(3, ["홍조"], ["정제수"]),
    ]
    result = recommend(profile(concerns=["건조/보습", "모공"]), products, [], [])
    ids = [r["id"] for r in result["recommended"]]
    assert ids == [2, 1, 3]
    top = result["recommended"][0]
    assert top["match_count"] == 2 and top["total_concerns"] == 2
    assert top["matched_concerns"] == ["건조/보습", "모공"]


def test_gate_failure_is_excluded_even_with_best_match():
    # 고민이 전부 맞아도 게이트를 통과 못하면 추천되지 않아야 함 (합산식이었다면 추천될 수 있는 경우)
    products = [
        make_product(1, ["건조/보습", "모공"], ["정제수", "향료"]),
        make_product(2, [], ["정제수"]),
    ]
    result = recommend(profile(is_sensitive=True, concerns=["건조/보습", "모공"]), products, IRRITANTS, [])
    assert [r["id"] for r in result["recommended"]] == [2]
    assert result["excluded"][0]["id"] == 1
    assert result["excluded"][0]["reasons"][0]["ingredient"] == "향료"


def test_preferred_ingredient_only_breaks_ties():
    products = [
        make_product(1, ["건조/보습"], ["정제수"]),
        make_product(2, ["건조/보습"], ["정제수", "나이아신아마이드"]),
        make_product(3, ["건조/보습", "모공"], ["정제수"]),
    ]
    result = recommend(
        profile(concerns=["건조/보습", "모공"], preferred_ingredients="나이아신아마이드"), products, [], []
    )
    assert [r["id"] for r in result["recommended"]] == [3, 2, 1]
    assert result["recommended"][1]["preferred_hits"] == ["나이아신아마이드"]


def test_unverified_products_skipped_by_default():
    products = [make_product(1, ["건조/보습"], ["정제수"], verified=False), make_product(2, [], ["정제수"])]
    result = recommend(profile(concerns=["건조/보습"]), products, [], [])
    assert [r["id"] for r in result["recommended"]] == [2]
    assert result["skipped_unverified"] == 1

    result = recommend(profile(concerns=["건조/보습"]), products, [], [], include_unverified=True)
    assert [r["id"] for r in result["recommended"]] == [1, 2]
    assert result["recommended"][0]["is_concerns_verified"] is False


# --- 2단계 정렬 (주력 매칭 → 핵심 계열 수 → 함유 매칭 → 선호 성분), 근거 부족 ---

def tag(family, *concerns):
    return {"family": family, "mains": list(concerns), "all": list(concerns), "exclude": False}


TAGS = {
    "알란토인": tag("진정 성분(홍조)", "홍조"),
    "병풀추출물": tag("병풀", "홍조"),
    "나이아신아마이드": tag("비타민B·나이아신·판테놀", "미백/톤"),
}
MARKERS = ["향료"]


def ids(result):
    return [r["id"] for r in result["recommended"]]


def test_core_family_count_breaks_ties_between_main_matches():
    # 둘 다 홍조가 주력이지만 경계(향료) 앞에 홍조 계열이 둘인 제품이 먼저
    products = [
        make_product(1, ["홍조"], ["정제수", "알란토인", "향료", "병풀추출물"]),
        make_product(2, ["홍조"], ["정제수", "알란토인", "병풀추출물", "향료"]),
    ]
    result = recommend(profile(concerns=["홍조"]), products, [], [], tags=TAGS, markers=MARKERS)
    assert ids(result) == [2, 1]


def test_contained_match_fills_after_main_matches():
    products = [
        make_product(1, ["건조/보습"], ["정제수", "알란토인"]),   # 주력은 아니지만 홍조 성분 함유
        make_product(2, ["홍조"], ["정제수", "알란토인"]),        # 주력 매칭
        make_product(3, ["건조/보습"], ["정제수"]),               # 매칭 없음
    ]
    result = recommend(profile(concerns=["홍조"]), products, [], [], tags=TAGS, markers=MARKERS)
    assert ids(result) == [2, 1, 3]
    types = {r["id"]: r["match_type"] for r in result["recommended"]}
    assert types == {2: MATCH_MAIN, 1: MATCH_CONTAINED, 3: MATCH_NONE}
    assert result["recommended"][1]["contained_matched"] == ["홍조"]


def test_main_basis_insufficient_product_goes_last_and_is_flagged():
    products = [
        make_product(1, [], ["정제수"]),                         # 검수 결과 주력 없음
        make_product(2, ["건조/보습"], ["정제수"]),
    ]
    result = recommend(profile(concerns=["홍조"]), products, [], [], tags=TAGS, markers=MARKERS)
    assert ids(result) == [2, 1]
    assert result["recommended"][1]["main_basis_insufficient"] is True
    assert result["recommended"][0]["main_basis_insufficient"] is False


def test_works_without_tag_tables():
    products = [make_product(1, ["홍조"], ["정제수"]), make_product(2, [], ["정제수"])]
    result = recommend(profile(concerns=["홍조"]), products, [], [])
    assert ids(result) == [1, 2]
