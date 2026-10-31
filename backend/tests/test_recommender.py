from app.services.recommender import (
    recommend, check_gates, find_warnings, split_ingredient_text,
    REASON_SENSITIVE, REASON_BANNED, REASON_AVOIDED,
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


def test_top_n_irritant_only_counts_in_front_section():
    names = ["정제수"] * 0 + [f"성분{i}" for i in range(1, 25)] + ["에탄올"]  # 에탄올 25번째
    p = make_product(1, [], names)
    assert check_gates(p, profile(is_sensitive=True), IRRITANTS, [], top_n=20) == []
    p_front = make_product(2, [], ["정제수", "에탄올"])
    assert check_gates(p_front, profile(is_sensitive=True), IRRITANTS, [], top_n=20)


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
    assert find_warnings(p, REGULATED) == [{"ingredient": "페녹시에탄올", "limit_cond": "1%"}]


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
