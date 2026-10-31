from app.services.concern_tagger import rank_concerns, tag_concerns, load_concern_map


def entry(name, concern, strength, rule="top_n", family=""):
    return {"ingredient_name": name, "concern": concern, "strength": strength,
            "position_rule": rule, "family": family or name}


def ings(*names):
    return [{"name": n, "position": i} for i, n in enumerate(names, start=1)]


def test_same_family_scored_once():
    cmap = [
        entry("소듐하이알루로네이트", "건조/보습", "strong", family="히알루론산"),
        entry("하이알루로닉애씨드", "건조/보습", "strong", family="히알루론산"),
        entry("판테놀", "건조/보습", "strong"),
    ]
    ranked = rank_concerns(ings("정제수", "소듐하이알루로네이트", "하이알루로닉애씨드", "판테놀"), cmap)
    # 히알루론산 계열 1회(2점) + 판테놀(2점) = 4점. 계열 보정이 없으면 6점
    assert ranked[0]["score"] == 4
    # 근거 성분은 전부 남김
    assert len(ranked[0]["hits"]) == 3


def test_weak_same_family_does_not_make_candidate():
    cmap = [
        entry("병풀추출물", "홍조", "weak", family="병풀"),
        entry("마데카소사이드", "홍조", "weak", family="병풀"),
    ]
    # 같은 계열 weak 2개는 "서로 다른 weak 2개" 조건을 채우지 못함
    assert rank_concerns(ings("병풀추출물", "마데카소사이드"), cmap) == []


def test_top_n_rule_ignores_back_section():
    cmap = [entry("글리세린", "건조/보습", "strong")]
    names = [f"성분{i}" for i in range(1, 21)] + ["글리세린"]
    assert rank_concerns(ings(*names), cmap, top_n=20) == []


def test_max_concerns_limit():
    cmap = [
        entry("A", "건조/보습", "strong"),
        entry("B", "모공", "strong"),
        entry("C", "홍조", "strong"),
    ]
    assert len(tag_concerns(ings("A", "B", "C"), cmap, max_concerns=2)) == 2


def test_real_map_loads_and_has_family():
    cmap = load_concern_map()
    assert all(e["family"] for e in cmap)
