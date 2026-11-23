# 제품별 주력 고민 초안을 사람이 훑어보며 검수하기 좋은 표(마크다운)로 만드는 스크립트
# 규칙(main_concerns.py)이 바뀌면 다시 실행해서 표를 새로 만들면 됨. DB에는 쓰지 않음
#
# 사용법 (backend 폴더에서):
#   python -m scripts.review_sheet
# 결과: data/review_sheet.md
#
# 검수 결과는 이 표가 아니라 data/main_concerns_draft.csv에 적음
#   - 초안이 맞으면 reviewed 칸에 o
#   - 고칠 때는 verified_concerns 칸에 고민을 콤마로 적고(없으면 "없음") reviewed에 o
import argparse
from pathlib import Path

from app.services.main_concerns import (
    MOISTURE, MOISTURE_MIN_FAMILIES, decide_main, load_markers, load_name_aliases, load_tags,
)
from scripts.load_products import read_rows, DEFAULT_CSV

DEFAULT_OUT = Path(__file__).resolve().parents[2] / "data" / "review_sheet.md"
EARLY_BOUNDARY = 6  # 경계가 이보다 앞이면 거의 모든 성분이 "소량 구간"이라 판정 근거가 얇음


def flags_for(result: dict, formulas: list[dict]) -> list[str]:
    flags = []
    if not result["main"]:
        flags.append("주력 근거 부족")
    for concern in result["main"]:
        e = result["evidence"][concern]
        if e["signal"] and not e["families"]:
            flags.append(f"{concern}: 제품명만 근거")
        elif concern == MOISTURE and not e["signal"] and len(e["families"]) == MOISTURE_MIN_FAMILIES:
            flags.append("건조/보습: 기준선 통과(딱 4개)")
    if any(est for _, _, est in result["boundaries"]):
        flags.append("경계 추정")
    if any(b <= EARLY_BOUNDARY for _, b, _ in result["boundaries"]):
        flags.append("경계가 앞쪽")
    if len(formulas) > 1:
        flags.append("2제형")
    return flags


def evidence_text(result: dict) -> str:
    if not result["main"]:
        return "-"
    parts = []
    for concern in result["main"]:
        e = result["evidence"][concern]
        names = ", ".join(n.split("[")[0] for n in e["names"][:4]) or "(제품명 신호만)"
        parts.append(f"**{concern}**{'(제품명)' if e['signal'] else ''}: {names}")
    return "<br>".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    tags, markers, aliases = load_tags(), load_markers(), load_name_aliases()
    products, _ = read_rows(args.csv)

    rows, flagged = [], 0
    for i, p in enumerate(products, start=1):
        result = decide_main(p["product_name"], p["formulas"], tags, markers, aliases)
        flags = flags_for(result, p["formulas"])
        flagged += bool(flags)
        rows.append((i, p, result, flags))

    lines = [
        "# 주력 고민 검수표",
        "",
        "> 검수 결과는 `data/main_concerns_draft.csv`의 `reviewed`(맞으면 o)와 `verified_concerns`(고칠 때만 적음, 고민 없음은 `없음`)에 적습니다.",
        "> 번호는 CSV의 행 순서와 같습니다. **확인할 것은 하나뿐입니다: 이 제품의 대표 고민이 맞는가?** (올리브영 상품 페이지의 제품 소개와 비교)",
        "",
        f"- 제품 {len(rows)}개 중 **주의 표시가 있는 제품 {flagged}개**는 먼저 보세요.",
        "- 주의 표시: `주력 근거 부족`(주력이 없음), `제품명만 근거`(성분은 경계 뒤라 제품명 신호만으로 정함), "
        "`기준선 통과(딱 4개)`(건조/보습이 기준을 겨우 넘음), `경계 추정`(소량 성분 표지가 없어 경계를 짐작함), "
        "`경계가 앞쪽`(대부분이 소량 구간), `2제형`(두 처방이 합쳐진 제품)",
        "- `함유만`: 성분은 들어 있지만 주력이 되지 못한 고민 (경계 뒤이거나 기준 미달)",
        "",
        "| # | 제품 | 카테고리 | 초안 주력 | 근거 성분(위치) | 함유만 | 주의 |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, p, result, flags in rows:
        lines.append(
            f"| {i} | {p['product_name']} | {p['category'] or ''} | {', '.join(result['main']) or '없음'} "
            f"| {evidence_text(result)} | {', '.join(result['contained']) or '-'} | {', '.join(flags) or '-'} |"
        )
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"제품 {len(rows)}개, 주의 표시 {flagged}개 → {args.out}")


if __name__ == "__main__":
    main()
