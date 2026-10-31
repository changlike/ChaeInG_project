# 제품의 성분표와 "성분→고민 사전"으로 제품의 주력 고민(main_concerns)을 판정하는 규칙
# LLM이 직접 판단하지 않고, 사람이 검수한 사전과 아래 규칙만으로 결과가 정해짐 (같은 입력 → 같은 결과)
import csv
from pathlib import Path

from app.schemas.profile import ALLOWED_CONCERNS

# 앞에서부터 몇 번째 성분까지를 "함량 순서가 의미 있는 구간"으로 볼지 (함량 의존형 성분에만 적용)
# 데이터 확인 결과 보존제 첫 등장 위치의 중앙값이 18이라 20으로 정함. 결과를 보며 조정할 수 있음
TOP_N = 20

# 한 고민이 "후보"가 되는 조건
#   - strong 계열이 1개 이상 있거나
#   - weak 계열이 서로 다른 계열로 2개 이상 있을 때
MIN_WEAK_HITS = 2

# 후보 고민의 점수 = strong 계열 2점 + weak 계열 1점
# 같은 계열(family, 예: 히알루론산 변형 10종)은 한 고민 안에서 1회만 반영함
#   → 변형 성분이 많이 들어간 제품의 점수가 부풀려지는 문제를 막기 위함
#   → 계열 안에 strong이 하나라도 있으면 그 계열은 strong으로 봄
STRONG_SCORE = 2
WEAK_SCORE = 1

# 제품당 최종으로 남기는 "주력 고민" 개수 (점수 높은 순)
# 건조/보습처럼 거의 모든 제품에 해당하는 고민이 전부 붙지 않게 하기 위함
MAX_CONCERNS = 2

# position_rule 값
RULE_TOP_N = "top_n"   # 앞쪽 TOP_N 안에 있을 때만 인정 (글리세린 같은 흔한 성분)
RULE_ANY = "any"       # 위치와 무관하게 인정 (소량으로도 쓰는 유효 성분)

DEFAULT_MAP_PATH = Path(__file__).resolve().parents[3] / "data" / "ingredient_concern_map.csv"


def load_concern_map(path: Path = DEFAULT_MAP_PATH) -> list[dict]:
    """사전 CSV를 읽어 [{ingredient_name, concern, strength, position_rule, family, basis}] 반환
    family가 비어 있으면 성분명 자체를 계열로 봄 (단독 성분)"""
    with open(path, encoding="utf-8-sig", newline="") as f:
        entries = [{k.strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]

    for e in entries:
        if e["concern"] not in ALLOWED_CONCERNS:
            raise ValueError(f"허용되지 않은 고민: {e['concern']} ({e['ingredient_name']})")
        if e["strength"] not in ("strong", "weak"):
            raise ValueError(f"strength 값 오류: {e}")
        if e["position_rule"] not in (RULE_TOP_N, RULE_ANY):
            raise ValueError(f"position_rule 값 오류: {e}")
        e["family"] = e.get("family") or e["ingredient_name"]
    return entries


def rank_concerns(ingredients: list[dict], concern_map: list[dict], top_n: int = TOP_N) -> list[dict]:
    """후보 고민을 점수 높은 순으로 반환. [{concern, score, hits:[{name, position, strength, family}]}]
    점수가 같으면 근거 성분이 더 앞쪽(함량 순서가 앞)에 있는 고민을 먼저, 그래도 같으면 ALLOWED_CONCERNS 순서."""
    position_of = {i["name"]: i["position"] for i in ingredients}

    evidence: dict[str, list[dict]] = {}
    for entry in concern_map:
        pos = position_of.get(entry["ingredient_name"])
        if pos is None:
            continue
        if entry["position_rule"] == RULE_TOP_N and pos > top_n:
            continue
        evidence.setdefault(entry["concern"], []).append(
            {
                "name": entry["ingredient_name"],
                "position": pos,
                "strength": entry["strength"],
                "family": entry.get("family") or entry["ingredient_name"],
            }
        )

    candidates = []
    for order, concern in enumerate(ALLOWED_CONCERNS):
        hits = evidence.get(concern, [])
        # 계열별로 묶어서 strong 계열 / weak 계열을 셈 (근거 성분 목록 hits는 전부 유지)
        family_strength: dict[str, str] = {}
        for h in hits:
            if family_strength.get(h["family"]) != "strong":
                family_strength[h["family"]] = h["strength"]
        strong = [f for f, st in family_strength.items() if st == "strong"]
        weak = [f for f, st in family_strength.items() if st == "weak"]
        if strong or len(weak) >= MIN_WEAK_HITS:
            hits = sorted(hits, key=lambda h: h["position"])
            score = len(strong) * STRONG_SCORE + len(weak) * WEAK_SCORE
            candidates.append(
                {"concern": concern, "score": score, "hits": hits, "_key": (-score, hits[0]["position"], order)}
            )

    candidates.sort(key=lambda c: c["_key"])
    for c in candidates:
        del c["_key"]
    return candidates


def tag_concerns(
    ingredients: list[dict], concern_map: list[dict], top_n: int = TOP_N, max_concerns: int = MAX_CONCERNS
) -> dict[str, list[dict]]:
    """제품의 주력 고민을 판정. {고민: [근거 성분 {name, position, strength}]} (점수 높은 순, 최대 max_concerns개)"""
    ranked = rank_concerns(ingredients, concern_map, top_n)
    return {c["concern"]: c["hits"] for c in ranked[:max_concerns]}
