# 제품의 주력 고민(main_concerns)을 판정하는 규칙 (docs/core-ingredient-rule.md 2-8)
# LLM이 판단하지 않고, 사람이 정한 성분 태그표와 아래 규칙만으로 결과가 정해짐 (같은 입력 → 같은 결과)
#
#   1. 제품명 신호가 있는 고민을 먼저 주력에 넣음
#   2. 제품별 "경계" 앞 성분의 계열(family) 수로 나머지를 정함 (같은 계열은 1번, 기반 보습제 제외, 대표 고민만 셈)
#      경계 = 처음 나오는 소량 성분(마커) 바로 앞. 마커가 없으면 성분 수의 절반 정도
#   3. 건조/보습은 4개 이상, 나머지 고민은 1개 이상이어야 후보 (제품명 신호가 있으면 무조건 후보)
#      단위는 계열이지만 넓은 계열(오일·당류·아미노산·단백질)은 서로 다른 성분 수로 셈
#   4. 후보가 여럿이면 제품명 신호 → 계열 수 → 성분표 앞 위치 순으로 최대 2개
# 점수를 합산하지 않고 개수와 순서만 사용함. 2제형 제품은 제마다 계산한 뒤 계열을 합침
import csv
import math
import re
from pathlib import Path

from app.schemas.profile import ALLOWED_CONCERNS

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
DEFAULT_TAGS_PATH = DATA_DIR / "ingredient_concern_tags_draft.csv"
DEFAULT_MARKERS_PATH = DATA_DIR / "dilution_markers.csv"
DEFAULT_ALIASES_PATH = DATA_DIR / "name_aliases.csv"

MOISTURE = "건조/보습"
MOISTURE_MIN_FAMILIES = 4   # 거의 모든 제품에 보습 성분이 있어서 "진짜 보습 제품"을 가르는 기준 (계열 또는 성분 수)
OTHER_MIN_FAMILIES = 1      # 나머지 고민은 특징 성분이라 1개면 충분

# 서로 다른 성분이 많이 묶인 넓은 계열은 계열 하나로 세면 오일·시어버터·스쿠알란처럼
# 서로 다른 보습 성분이 여럿 든 제품도 1개로 보이므로, 이 계열은 서로 다른 성분 수로 셈함
# (히알루론산처럼 같은 성분의 변형이 많은 좁은 계열은 계열 1개로 셈)
BROAD_FAMILIES = {"오일·에몰리언트·왁스", "당류·보습 폴리올", "아미노산·베타인·엑토인", "콜라겐·엘라스틴·단백질"}
MAX_MAIN = 2
FALLBACK_RATIO = 0.5        # 마커가 없는 제품의 경계: 성분 수의 절반 정도 (임의로 정한 기준)

KIND_INGREDIENT = "성분"
KIND_CONCERN = "고민"


def _read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def load_tags(path: Path = DEFAULT_TAGS_PATH) -> dict[str, dict]:
    """성분 태그표 → {성분명: {family, mains:[대표 고민], exclude:bool}}
    대표 고민(main_concerns)만 주력 판정에 쓰고, 나머지 태그는 함유로만 남음"""
    tags = {}
    for row in _read(path):
        mains = [c for c in row.get("main_concerns", "").split("|") if c]
        bad = [c for c in mains if c not in ALLOWED_CONCERNS]
        if bad:
            raise ValueError(f"허용되지 않은 고민: {bad} ({row['ingredient_name']})")
        tags[row["ingredient_name"]] = {
            "family": row.get("family", ""),
            "mains": mains,
            "all": [c for c in row.get("tag_concerns", "").split("|") if c],
            "exclude": row.get("exclude_from_main", "") == "Y",
        }
    return tags


def load_markers(path: Path = DEFAULT_MARKERS_PATH) -> list[str]:
    """소량 성분(마커) 이름 조각 목록. 이름에 이 조각이 들어 있으면 마커로 봄"""
    return [row["ingredient_name"] for row in _read(path) if row.get("ingredient_name")]


def load_name_aliases(path: Path = DEFAULT_ALIASES_PATH) -> list[dict]:
    """제품명 별칭표 → [{pattern, kind, target}]. kind는 '성분'(성분명 조각 또는 계열 이름) 또는 '고민'"""
    aliases = []
    for row in _read(path):
        if row["kind"] not in (KIND_INGREDIENT, KIND_CONCERN):
            raise ValueError(f"kind 값 오류: {row}")
        if row["kind"] == KIND_CONCERN and row["target"] not in ALLOWED_CONCERNS:
            raise ValueError(f"허용되지 않은 고민: {row}")
        aliases.append({"pattern": re.compile(row["alias"], re.IGNORECASE), "kind": row["kind"], "target": row["target"]})
    return aliases


def find_boundary(ingredients: list[dict], markers: list[str]) -> tuple[int, bool]:
    """제품별 경계 위치와 추정 여부. 경계 앞(<= 경계) 성분의 순서만 함량 순서로 믿음.
    처음 나오는 마커 바로 앞까지가 경계이고, 마커가 없으면 성분 수의 절반 정도로 추정함"""
    positions = [i["position"] for i in ingredients if any(m in i["name"] for m in markers)]
    if positions:
        return max(min(positions) - 1, 1), False
    return max(math.ceil(len(ingredients) * FALLBACK_RATIO), 1), True


def name_signal(product_name: str, ingredients: list[dict], tags: dict[str, dict], aliases: list[dict]) -> list[str]:
    """제품명에서 읽은 고민 신호 (성분 근거가 실제 있을 때만 인정, 위치는 상관없음)"""
    found = []
    tagged = [(i, tags[i["name"]]) for i in ingredients if i["name"] in tags and tags[i["name"]]["mains"]]
    for alias in aliases:
        if not alias["pattern"].search(product_name):
            continue
        for ing, tag in tagged:
            if alias["kind"] == KIND_INGREDIENT:
                matched = alias["target"] in ing["name"] or tag["family"] == alias["target"]
                concerns = tag["mains"] if matched else []
            else:
                concerns = [alias["target"]] if alias["target"] in tag["mains"] else []
            for c in concerns:
                if c not in found:
                    found.append(c)
    return found


def _formula_stats(ingredients: list[dict], tags: dict[str, dict], markers: list[str]) -> dict:
    boundary, estimated = find_boundary(ingredients, markers)
    stats: dict[str, dict] = {}
    for ing in ingredients:
        tag = tags.get(ing["name"])
        # 경계 뒤 성분은 주력을 정하지 못하고(주력 보호), 기반 보습제는 제외
        if not tag or tag["exclude"] or ing["position"] > boundary:
            continue
        for concern in tag["mains"]:
            s = stats.setdefault(concern, {"families": set(), "first": ing["position"], "names": []})
            unit = ing["name"] if tag["family"] in BROAD_FAMILIES else (tag["family"] or ing["name"])
            s["families"].add(unit)
            s["first"] = min(s["first"], ing["position"])
            s["names"].append(f"{ing['name']}@{ing['position']}")
    return {"boundary": boundary, "estimated": estimated, "stats": stats}


def decide_main(
    product_name: str,
    formulas: list[dict],
    tags: dict[str, dict],
    markers: list[str],
    aliases: list[dict],
) -> dict:
    """제품의 주력 고민을 판정. formulas는 parse_formulas의 결과 ([{formula, ingredients}]).
    반환: {main:[고민], evidence:{고민:{signal, families, names}}, contained:[함유만 있는 고민],
           boundaries:[(제, 경계, 추정)], signal:[제품명 신호 고민]}"""
    all_ings = [i for f in formulas for i in f["ingredients"]]
    signal = name_signal(product_name, all_ings, tags, aliases)

    merged: dict[str, dict] = {}
    boundaries = []
    for f in formulas:
        result = _formula_stats(f["ingredients"], tags, markers)
        boundaries.append((f["formula"], result["boundary"], result["estimated"]))
        for concern, s in result["stats"].items():
            m = merged.setdefault(concern, {"families": set(), "first": s["first"], "names": []})
            m["families"] |= s["families"]
            m["first"] = min(m["first"], s["first"])
            m["names"] += [f"{n}[{f['formula']}제]" if len(formulas) > 1 else n for n in s["names"]]

    def passes(concern: str) -> bool:
        need = MOISTURE_MIN_FAMILIES if concern == MOISTURE else OTHER_MIN_FAMILIES
        return concern in signal or len(merged.get(concern, {}).get("families", ())) >= need

    candidates = [c for c in ALLOWED_CONCERNS if passes(c)]

    def key(c: str):
        s = merged.get(c, {"families": (), "first": 10**6})
        return (0 if c in signal else 1, -len(s["families"]), s["first"], ALLOWED_CONCERNS.index(c))

    main = sorted(candidates, key=key)[:MAX_MAIN]

    # 함유만 있는 고민: 대표 태그든 부가 태그든 성분이 제품에 있지만 주력은 아닌 고민
    present = []
    for ing in all_ings:
        tag = tags.get(ing["name"])
        if tag:
            for c in tag["all"]:
                if c not in present:
                    present.append(c)
    contained = [c for c in ALLOWED_CONCERNS if c in present and c not in main]

    evidence = {
        c: {
            "signal": c in signal,
            "families": sorted(merged.get(c, {}).get("families", ())),
            "names": merged.get(c, {}).get("names", []),
        }
        for c in main
    }
    return {"main": main, "evidence": evidence, "contained": contained, "boundaries": boundaries, "signal": signal}
