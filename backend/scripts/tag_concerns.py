# 성분 태그표와 주력 판정 규칙(app/services/main_concerns.py)으로 제품별 주력 고민 "초안"을 만들어
# 검수용 CSV로 저장하는 스크립트. DB에는 쓰지 않음 (사람이 검수한 뒤 apply_concerns로 반영)
#
# 사용법 (backend 폴더에서):
#   python -m scripts.tag_concerns
# 결과: data/main_concerns_draft.csv
import argparse
import csv
from collections import Counter
from pathlib import Path

from app.services.main_concerns import (
    MAX_MAIN, MOISTURE_MIN_FAMILIES, decide_main, load_markers, load_name_aliases, load_tags,
)
from scripts.load_products import read_rows, DEFAULT_CSV

DEFAULT_OUT = Path(__file__).resolve().parents[2] / "data" / "main_concerns_draft.csv"


def format_evidence(result: dict) -> str:
    # 예: 건조/보습[제품명 · 3계열]: 히알루론산·세라마이드·베타인 (소듐하이알루로네이트@7, …) | 홍조[1계열]: 진정 (알란토인@12)
    if not result["main"]:
        return "주력 근거 부족"
    parts = []
    for concern in result["main"]:
        e = result["evidence"][concern]
        label = ("제품명 · " if e["signal"] else "") + f"{len(e['families'])}계열"
        parts.append(f"{concern}[{label}]: {'·'.join(e['families'])} ({', '.join(e['names'][:6])})")
    return " | ".join(parts)


def format_boundary(result: dict) -> str:
    return " / ".join(
        f"{'' if len(result['boundaries']) == 1 else str(n) + '제 '}경계 {b}번째{' (추정)' if est else ''}"
        for n, b, est in result["boundaries"]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--force", action="store_true", help="검수 내용이 있어도 덮어씀")
    args = parser.parse_args()

    # 검수를 시작한 CSV를 실수로 덮어써서 검수 칸이 지워지는 일을 막음
    if args.out.exists() and not args.force:
        with open(args.out, encoding="utf-8-sig", newline="") as f:
            reviewed = [
                r for r in csv.DictReader(f)
                if (r.get("reviewed") or "").strip() or (r.get("verified_concerns") or "").strip()
            ]
        if reviewed:
            print(f"{args.out}에 검수한 행이 {len(reviewed)}개 있어 덮어쓰지 않습니다. "
                  "다른 이름으로 저장하려면 --out, 그래도 덮어쓰려면 --force")
            return

    tags, markers, aliases = load_tags(), load_markers(), load_name_aliases()
    products, _ = read_rows(args.csv)

    counter, first, none, with_signal = Counter(), Counter(), 0, 0
    rows = []
    for p in products:
        result = decide_main(p["product_name"], p["formulas"], tags, markers, aliases)
        main_list = result["main"]
        counter.update(main_list)
        if main_list:
            first[main_list[0]] += 1
        else:
            none += 1
        with_signal += bool(result["signal"])
        rows.append({
            "product_name": p["product_name"],
            "category": p["category"],
            "source_url": p["source_url"],
            "draft_concerns": ",".join(main_list),
            "evidence": format_evidence(result),
            # 성분은 있지만 경계 뒤이거나 기준에 못 미쳐 주력이 되지 못한 고민 (검수 때 참고)
            "contained_only": ",".join(result["contained"]),
            "boundary": format_boundary(result),
            # 검수 후 사람이 채우는 칸: 확정할 고민(콤마 구분). 비워 두고 reviewed만 표시하면 초안을 그대로 승인
            "verified_concerns": "",
            "reviewed": "",
        })

    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"제품 {len(products)}개 (건조/보습 {MOISTURE_MIN_FAMILIES}개 이상, 제품당 최대 {MAX_MAIN}개) → {args.out}")
    print("  주력에 포함된 제품 수 / 1순위:")
    for concern, n in counter.most_common():
        print(f"    {concern}: {n}개 / {first[concern]}개")
    print(f"  제품명 신호가 있는 제품: {with_signal}개")
    print(f"  주력 근거 부족: {none}개")


if __name__ == "__main__":
    main()
