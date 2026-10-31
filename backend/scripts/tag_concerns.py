# 성분→고민 사전으로 제품별 주력 고민 "초안"을 만들어 검수용 CSV로 저장하는 스크립트
# DB에는 쓰지 않음 (사람이 검수한 뒤 별도로 반영)
#
# 사용법 (backend 폴더에서):
#   python -m scripts.tag_concerns
# 결과: data/main_concerns_draft.csv
import argparse
import csv
from collections import Counter
from pathlib import Path

from app.services.concern_tagger import load_concern_map, rank_concerns, TOP_N, MAX_CONCERNS
from scripts.load_products import read_rows, DEFAULT_CSV

DEFAULT_OUT = Path(__file__).resolve().parents[2] / "data" / "main_concerns_draft.csv"


def format_evidence(ranked: list[dict]) -> str:
    # 예: 건조/보습[7점]: 판테놀(10,strong) · 글리세린(3,weak) | 미백/톤[4점]: 나이아신아마이드(5,strong)
    parts = []
    for c in ranked:
        hit_text = " · ".join(f"{h['name']}({h['position']},{h['strength']})" for h in c["hits"])
        parts.append(f"{c['concern']}[{c['score']}점]: {hit_text}")
    return " | ".join(parts)


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

    concern_map = load_concern_map()
    products, _ = read_rows(args.csv)

    # 사전에 있는데 데이터에 한 번도 없는 성분 (오타나 표기 차이 점검용)
    all_names = {i["name"] for p in products for i in p["ingredients"]}
    missing = sorted({e["ingredient_name"] for e in concern_map} - all_names)

    counter, untagged = Counter(), 0
    rows = []
    for p in products:
        ranked = rank_concerns(p["ingredients"], concern_map)
        selected, cut = ranked[:MAX_CONCERNS], ranked[MAX_CONCERNS:]
        counter.update(c["concern"] for c in selected)
        if not selected:
            untagged += 1
        rows.append({
            "product_name": p["product_name"],
            "category": p["category"],
            "source_url": p["source_url"],
            "draft_concerns": ",".join(c["concern"] for c in selected),
            "evidence": format_evidence(selected),
            # 후보였지만 상위 개수 제한으로 빠진 고민 (검수 때 참고)
            "cut_candidates": " | ".join(f"{c['concern']}[{c['score']}점]" for c in cut),
            # 검수 후 사람이 채우는 칸: 확정할 고민(콤마 구분). 비워 두면 초안을 그대로 쓰지 않음
            "verified_concerns": "",
            "reviewed": "",
        })

    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"제품 {len(products)}개 (TOP_N={TOP_N}, 제품당 최대 {MAX_CONCERNS}개) → {args.out}")
    for concern, n in counter.most_common():
        print(f"  {concern}: {n}개")
    print(f"  판정된 고민 없음: {untagged}개")
    if missing:
        print(f"사전에는 있으나 현재 데이터에 없는 성분 {len(missing)}개: {', '.join(missing)}")


if __name__ == "__main__":
    main()
