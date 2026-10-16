# 통합 CSV를 DB(products, ingredients, product_ingredients)에 적재하는 스크립트
# 여러 번 실행해도 결과가 같도록(멱등) 제품은 source_url 기준으로 갱신함
#
# 사용법 (backend 폴더에서):
#   python -m scripts.load_products --dry-run     # DB에 쓰지 않고 파싱 결과만 확인
#   python -m scripts.load_products               # 실제 적재
import argparse
import csv
from pathlib import Path

from app.services.ingredient_parser import (
    MAX_NAME_LENGTH, parse_ingredients, clean_source_url, review_reason,
)

DEFAULT_CSV = Path(__file__).resolve().parents[2] / "data" / "ChaeInG_data - 통합.csv"


def read_rows(csv_path: Path) -> tuple[list[dict], list[str]]:
    """CSV를 읽어 정리된 제품 dict 목록과 경고 목록을 반환"""
    warnings, products, seen_urls = [], [], set()

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):
            # 헤더/값의 앞뒤 공백 제거 (예: "source_url ", "토리든 ")
            row = {(k or "").strip(): (v or "").strip() for k, v in row.items()}

            name = row.get("product_name", "")
            if not name:
                warnings.append(f"{line_no}행: 제품명이 비어 있어 건너뜀")
                continue

            url = clean_source_url(row.get("source_url", ""))
            if not url:
                warnings.append(f"{line_no}행 [{name}]: source_url이 비어 있어 건너뜀")
                continue
            if "goodsNo=" not in url:
                warnings.append(f"{line_no}행 [{name}]: goodsNo를 찾지 못해 원본 URL 유지")
            if url in seen_urls:
                warnings.append(f"{line_no}행 [{name}]: 같은 URL이 이미 있어 건너뜀")
                continue
            seen_urls.add(url)

            raw_ingredients = row.get("full_ingredients", "")
            reason = review_reason(raw_ingredients)
            if reason:
                # 잘못 쪼개진 성분이 DB에 들어가는 것보다 빠지는 편이 낫다고 판단 → CSV 수정 후 재실행
                warnings.append(f"{line_no}행 [{name}]: 수기 확인 필요, 적재 제외 ({reason})")
                continue

            ingredients = parse_ingredients(raw_ingredients)
            if not ingredients:
                warnings.append(f"{line_no}행 [{name}]: 성분 목록이 비어 있음")
            for ing in ingredients:
                if len(ing["name"]) > MAX_NAME_LENGTH:
                    warnings.append(
                        f"{line_no}행 [{name}]: 성분명이 {MAX_NAME_LENGTH}자 초과 → {ing['name'][:30]}..."
                    )

            products.append({
                "product_name": name,
                "brand": row.get("brand") or None,
                "category": row.get("category") or None,
                "skin_type_target": row.get("skin_type_target") or None,
                "source_url": url,
                # main_concern은 LLM 초안 + 검수 후 별도로 채움.
                # CSV의 '확인' 컬럼은 데이터 확인 표시라 사용하지 않음
                "main_concerns": row.get("main_concern") or None,
                "ingredients": ingredients,
            })
    return products, warnings


def load(products: list[dict]):
    # DB 관련 import는 실제 적재 때만 함 (dry-run은 DB 없이도 돌아가도록)
    from app.core.database import SessionLocal
    from app.models.product import Product, Ingredient, ProductIngredient

    db = SessionLocal()
    created = updated = 0
    try:
        ingredient_cache = {i.ingredient_name: i for i in db.query(Ingredient).all()}

        for data in products:
            product = db.query(Product).filter(Product.source_url == data["source_url"]).first()
            if product is None:
                product = Product(source_url=data["source_url"])
                db.add(product)
                created += 1
            else:
                updated += 1

            product.product_name = data["product_name"]
            product.brand = data["brand"]
            product.category = data["category"]
            product.skin_type_target = data["skin_type_target"]
            # 이미 검수된 주력 고민은 CSV가 비어 있어도 지우지 않음
            if data["main_concerns"] and not product.is_concerns_verified:
                product.main_concerns = data["main_concerns"]
            db.flush()  # product.id 확보

            # 성분 연결은 통째로 교체 (순서가 바뀌었을 수 있으므로)
            db.query(ProductIngredient).filter(
                ProductIngredient.product_id == product.id
            ).delete()
            for ing in data["ingredients"]:
                ingredient = ingredient_cache.get(ing["name"])
                if ingredient is None:
                    ingredient = Ingredient(ingredient_name=ing["name"])
                    db.add(ingredient)
                    db.flush()
                    ingredient_cache[ing["name"]] = ingredient
                db.add(ProductIngredient(
                    product_id=product.id,
                    ingredient_id=ingredient.id,
                    position=ing["position"],
                    amount_note=ing["amount_note"],
                ))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return created, updated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    products, warnings = read_rows(args.csv)
    total_ingredients = sum(len(p["ingredients"]) for p in products)
    unique_ingredients = len({i["name"] for p in products for i in p["ingredients"]})
    print(f"제품 {len(products)}개, 성분 연결 {total_ingredients}건, 고유 성분 {unique_ingredients}개")
    for w in warnings:
        print("경고:", w)

    if args.dry_run:
        return
    created, updated = load(products)
    print(f"적재 완료: 신규 {created}개, 갱신 {updated}개")


if __name__ == "__main__":
    main()
