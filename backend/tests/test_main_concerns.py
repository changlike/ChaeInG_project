import re

from app.services.main_concerns import decide_main, find_boundary, name_signal

MARKERS = ["페녹시에탄올", "향료"]


def tag(family, *mains, exclude=False):
    return {"family": family, "mains": list(mains), "all": list(mains), "exclude": exclude}


TAGS = {
    "소듐하이알루로네이트": tag("히알루론산", "건조/보습"),
    "하이알루로닉애씨드": tag("히알루론산", "건조/보습"),
    "세라마이드엔피": tag("세라마이드·장벽지질", "건조/보습"),
    "콜레스테롤": tag("세라마이드·장벽지질", "건조/보습"),
    "판테놀": tag("비타민B·나이아신·판테놀", "건조/보습"),
    # 넓은 계열: 서로 다른 성분 수로 셈
    "베타인": tag("아미노산·베타인·엑토인", "건조/보습"),
    "알지닌": tag("아미노산·베타인·엑토인", "건조/보습"),
    "스쿠알란": tag("오일·에몰리언트·왁스", "건조/보습"),
    "시어버터": tag("오일·에몰리언트·왁스", "건조/보습"),
    "호호바오일": tag("오일·에몰리언트·왁스", "건조/보습"),
    "글리세린": tag("용제·글라이콜", "건조/보습", exclude=True),
    "나이아신아마이드": tag("비타민B·나이아신·판테놀", "미백/톤"),
    "알란토인": tag("진정 성분(홍조)", "홍조"),
    "레티놀": tag("레티노이드·바쿠치올", "주름/탄력"),
}
ALIASES = [
    {"pattern": re.compile("나이아신"), "kind": "성분", "target": "나이아신아마이드"},
    {"pattern": re.compile("수분|보습"), "kind": "고민", "target": "건조/보습"},
]


def formula(*names, number=1):
    return {"formula": number, "ingredients": [{"position": i + 1, "name": n, "amount_note": None} for i, n in enumerate(names)]}


def decide(name, *formulas):
    return decide_main(name, list(formulas), TAGS, MARKERS, ALIASES)


def test_boundary_is_before_first_marker():
    f = formula("정제수", "글리세린", "향료", "알란토인")["ingredients"]
    assert find_boundary(f, MARKERS) == (2, False)


def test_boundary_falls_back_to_half_when_no_marker():
    f = formula("a", "b", "c", "d", "e", "f")["ingredients"]
    assert find_boundary(f, MARKERS) == (3, True)


def test_moisture_needs_four():
    three = formula("정제수", "소듐하이알루로네이트", "세라마이드엔피", "판테놀", "향료")
    four = formula("정제수", "소듐하이알루로네이트", "세라마이드엔피", "판테놀", "베타인", "향료")
    assert decide("크림", three)["main"] == []
    assert decide("크림", four)["main"] == ["건조/보습"]


def test_same_narrow_family_counts_once():
    # 히알루론산 두 개 = 1계열 → 히알루론산·세라마이드·판테놀 = 3 → 기준(4)에 못 미침
    f = formula("정제수", "소듐하이알루로네이트", "하이알루로닉애씨드", "세라마이드엔피", "판테놀", "향료")
    assert decide("크림", f)["main"] == []


def test_broad_family_counts_distinct_ingredients():
    # 오일 계열 성분 3개는 3으로 셈 → 오일 3 + 히알루론산 1 = 4
    f = formula("정제수", "스쿠알란", "시어버터", "호호바오일", "소듐하이알루로네이트", "향료")
    assert decide("크림", f)["main"] == ["건조/보습"]


def test_base_moisturizer_is_excluded():
    f = formula("정제수", "글리세린", "소듐하이알루로네이트", "세라마이드엔피", "판테놀", "향료")
    assert decide("크림", f)["main"] == []


def test_other_concerns_need_one():
    f = formula("정제수", "알란토인", "향료")
    assert decide("앰플", f)["main"] == ["홍조"]


def test_ingredient_after_boundary_cannot_decide_main():
    # 경계(향료) 뒤의 나이아신아마이드는 주력이 못 되고 함유로만 남음
    f = formula("정제수", "알란토인", "향료", "나이아신아마이드")
    result = decide("앰플", f)
    assert result["main"] == ["홍조"]
    assert "미백/톤" in result["contained"]


def test_extra_ingredient_does_not_change_main():
    # 나이아신아마이드가 주력인 제품에 보습 성분이 소량 더 있어도 주력이 바뀌지 않음
    f = formula("정제수", "나이아신아마이드", "향료", "알지닌")
    assert decide("나이아신 세럼", f)["main"] == ["미백/톤"]


def test_product_name_signal_comes_first():
    f = formula("정제수", "알란토인", "나이아신아마이드", "레티놀", "향료")
    assert decide("나이아신 세럼", f)["main"][0] == "미백/톤"


def test_concern_word_in_name_needs_ingredient_support():
    f = formula("정제수", "알란토인", "향료")
    assert name_signal("수분 앰플", f["ingredients"], TAGS, ALIASES) == []
    g = formula("정제수", "알란토인", "향료", "베타인")
    assert name_signal("수분 앰플", g["ingredients"], TAGS, ALIASES) == ["건조/보습"]


def test_main_is_limited_to_two_and_ordered_by_count():
    f = formula(
        "정제수", "소듐하이알루로네이트", "세라마이드엔피", "판테놀", "베타인", "스쿠알란",
        "알란토인", "레티놀", "향료",
    )
    assert decide("크림", f)["main"] == ["건조/보습", "홍조"]


def test_two_part_formula_merges_families():
    one = formula("정제수", "소듐하이알루로네이트", "세라마이드엔피", "판테놀", "향료", number=1)
    two = formula("정제수", "베타인", "향료", number=2)
    assert decide("듀얼 크림", one, two)["main"] == ["건조/보습"]
