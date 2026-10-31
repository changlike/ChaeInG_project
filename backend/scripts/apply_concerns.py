# 검수용 CSV(data/main_concerns_draft.csv)의 결과를 DB products.main_concerns에 반영하는 스크립트
#
# 검수 방법 (CSV에서 사람이 직접):
#   - reviewed 칸에 아무 표시(o 등)를 하면 "검수 완료"
#   - verified_concerns 칸을 채우면 그 값을 확정값으로 씀 (콤마 구분, 6개 고민 어휘만)
#   - verified_concerns를 비워 두고 reviewed만 표시하면 "초안(draft_concerns)을 그대로 승인"으로 봄
#   - 고민이 없다고 확정하려면 verified_concerns에 "없음"
#
# 사용법 (backend 폴더에서):
#   python -m scripts.apply_concerns --dry-run        # DB에 쓰지 않고 반영 예정 내용만 확인
#   python -m scripts.apply_concerns                  # 검수 완료 행만 반영 (is_concerns_verified=True)
#   python -m scripts.apply_concerns --with-drafts    # 검수 전 행도 초안으로 반영 (is_concerns_verified=False)
#
# 검수 전 초안은 추천 엔진이 기본적으로 사용하지 않음 (data-and-llm-policy.md 원칙 1)
import argparse
import csv
from pathlib import Path

from app.schemas.profile import ALLOWED_CONCERNS

DEFAULT_DRAFT = Path(__file__).resolve().parents[2] / "data" / "main_concerns_draft.csv"
NO_CONCERN = "없음"


def parse_concerns(text: str) -> list[str]:
    """콤마 문자열 → 고민 목록. 허용 어휘 밖의 값이 있으면 ValueError"""
    values = [v.strip() for v in (text or "").split(",") if v.strip()]
    if values == [NO_CONCERN]:
        return []
    invalid = [v for v in values if v not in ALLOWED_CONCERNS]
    if invalid:
        raise ValueError(f"허용되지 않은 고민: {invalid}")
    # 순서 유지 + 중복 제거
    return list(dict.fromkeys(values))


def build_updates(rows: list[dict], with_drafts: bool = False) -> tuple[list[dict], list[str]]:
    """검수 CSV 행 → [{source_url, main_concerns(list), verified(bool)}], 오류 목록"""
    updates, errors = [], []
    for line_no, row in enumerate(rows, start=2):
        url = (row.get("source_url") or "").strip()
        reviewed = bool((row.get("reviewed") or "").strip())
        verified_text = (row.get("verified_concerns") or "").strip()

        if reviewed:
            source_text, verified = (verified_text or row.get("draft_concerns", "")), True
        elif with_drafts:
            source_text, verified = row.get("draft_concerns", ""), False
        else:
            continue

        try:
            concerns = parse_concerns(source_text)
        except ValueError as e:
            errors.append(f"{line_no}행 [{row.get('product_name')}]: {e}")
            continue
        updates.append({"source_url": url, "main_concerns": concerns, "verified": verified})
    return updates, errors


def apply(updates: list[dict]) -> tuple[int, list[str]]:
    from app.core.database import SessionLocal
    from app.models.product import Product

    db = SessionLocal()
    applied, not_found = 0, []
    try:
        for u in updates:
            product = db.query(Product).filter(Product.source_url == u["source_url"]).first()
            if product is None:
                not_found.append(u["source_url"])
                continue
            # 이미 검수된 값은 초안으로 덮어쓰지 않음
            if product.is_concerns_verified and not u["verified"]:
                continue
            product.main_concerns = ",".join(u["main_concerns"]) or None
            product.is_concerns_verified = u["verified"]
            applied += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return applied, not_found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", type=Path, default=DEFAULT_DRAFT)
    parser.add_argument("--with-drafts", action="store_true", help="검수 전 행도 초안 상태로 반영")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(args.draft, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    updates, errors = build_updates(rows, with_drafts=args.with_drafts)
    n_verified = sum(u["verified"] for u in updates)
    print(f"반영 대상 {len(updates)}개 (검수 완료 {n_verified}개, 초안 {len(updates) - n_verified}개)")
    for e in errors:
        print("오류:", e)
    if errors:
        print("오류가 있어 반영하지 않습니다. CSV를 고친 뒤 다시 실행하세요.")
        return
    if args.dry_run:
        return

    applied, not_found = apply(updates)
    print(f"반영 완료: {applied}개")
    for url in not_found:
        print("DB에 없는 제품:", url)


if __name__ == "__main__":
    main()
