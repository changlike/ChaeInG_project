# 해석기(LLM + 코드 검증) 정확도 평가 스크립트
# 정답은 scripts/eval_cases.py에 사람이 적은 값이고, 실제 LLM을 호출하므로 OpenAI 키가 필요함 (비용이 들고 결과가 조금씩 다를 수 있음)
# 단위 테스트(pytest)는 LLM을 가짜로 바꿔 쓰고, 이 평가는 따로 실행함
#
# 사용법 (backend 폴더에서):
#   python -m scripts.eval_interpreter                          # 표만 출력
#   python -m scripts.eval_interpreter --out ../docs/eval-results.md   # 결과를 마크다운으로도 저장
#
# 지표
#   문장 유형 일치율 : intent가 정답과 같은가
#   고민 일치율     : 고민 집합이 정답과 정확히 같은가
#   카테고리 일치율  : 카테고리가 같은가
#   기피 성분 재현율 : 정답의 기피 성분이 해석 결과에 빠짐없이 들어 있는가 (안전과 직결되어 정밀도보다 우선)
#   선호 성분 재현율 : 같은 방식
import argparse
from collections import defaultdict
from pathlib import Path

from app.services.llm.client import chat_json
from app.services.llm.interpreter import INTENT_RECOMMEND, _clean_names, interpret
from scripts.eval_cases import CASES


def grade(case: dict, got: dict) -> dict:
    """한 케이스를 채점. 정답에 적힌 항목만 보고 {항목: (맞음, 기대값, 실제값)}를 돌려줌"""
    expect, results = case["expect"], {}
    if "intent" in expect:
        results["intent"] = (got["intent"] == expect["intent"], expect["intent"], got["intent"])
    if "concerns" in expect:
        results["concerns"] = (set(got["concerns"]) == expect["concerns"], sorted(expect["concerns"]), sorted(got["concerns"]))
    if "category" in expect:
        results["category"] = (got["category"] == expect["category"], expect["category"], got["category"])
    for key, field in (("avoided", "avoided"), ("preferred", "preferred")):
        if key in expect:
            wanted = set(_clean_names(list(expect[key])))
            missing = wanted - set(got[field])
            results[key] = (not missing, sorted(wanted), got[field])
    return results


def run(cases: list[dict]) -> list[dict]:
    rows = []
    for case in cases:
        got, notices = interpret(case["message"], case.get("previous"), chat_json)
        if got is None:  # LLM 호출 실패 (키 없음, 시간 초과 등)
            rows.append({"case": case, "error": notices[0] if notices else "호출 실패", "results": {}})
            continue
        rows.append({"case": case, "got": got, "notices": notices, "results": grade(case, got)})
    return rows


def summarize(rows: list[dict]) -> dict:
    """지표별 (맞은 수, 전체 수)와 묶음별 케이스 통과 수"""
    metrics = defaultdict(lambda: [0, 0])
    groups = defaultdict(lambda: [0, 0])
    for r in rows:
        passed = bool(r["results"]) and all(ok for ok, _, _ in r["results"].values())
        g = groups[r["case"]["group"]]
        g[0] += passed
        g[1] += 1
        for key, (ok, _, _) in r["results"].items():
            metrics[key][0] += ok
            metrics[key][1] += 1
    return {"metrics": dict(metrics), "groups": dict(groups), "errors": sum("error" in r for r in rows), "total": len(rows)}


METRIC_LABELS = {
    "intent": "문장 유형 일치율",
    "concerns": "고민 일치율 (집합이 정확히 같음)",
    "category": "카테고리 일치율",
    "avoided": "기피 성분 재현율",
    "preferred": "선호 성분 재현율",
}


def render(rows: list[dict], summary: dict) -> str:
    lines = ["# 해석기 평가 결과", "",
             f"테스트 문장 {summary['total']}개 (정답은 `backend/scripts/eval_cases.py`). 실제 LLM 호출 결과이며 실행할 때마다 조금씩 다를 수 있음.", ""]
    if summary["errors"]:
        lines += [f"> LLM 호출 실패 {summary['errors']}개는 채점에서 제외됨", ""]
    lines += ["## 지표", "", "| 지표 | 맞은 수 / 전체 |", "|---|---|"]
    for key, label in METRIC_LABELS.items():
        if key in summary["metrics"]:
            ok, total = summary["metrics"][key]
            lines.append(f"| {label} | {ok} / {total} |")
    lines += ["", "## 묶음별 통과", "", "| 묶음 | 통과 / 전체 |", "|---|---|"]
    for name, (ok, total) in summary["groups"].items():
        lines.append(f"| {name} | {ok} / {total} |")
    fails = [r for r in rows if "error" not in r and not all(ok for ok, _, _ in r["results"].values())]
    lines += ["", "## 틀린 사례", ""]
    if not fails:
        lines.append("없음")
    for r in fails:
        c = r["case"]
        lines.append(f"- **{c['id']}** ({c['group']}) \"{c['message']}\"")
        for key, (ok, want, got) in r["results"].items():
            if not ok:
                lines.append(f"  - {METRIC_LABELS.get(key, key)}: 기대 {want} / 실제 {got}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None, help="결과를 저장할 마크다운 파일")
    args = parser.parse_args()

    rows = run(CASES)
    summary = summarize(rows)
    text = render(rows, summary)
    print(text)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"저장: {args.out}")


if __name__ == "__main__":
    main()
