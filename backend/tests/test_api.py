# 회원가입 → 프로필 → 제품 검색 → 찜 → 추천까지 API 흐름 테스트 (SQLite, conftest.py 참고)
from app.models.product import Product, Ingredient, ProductIngredient


def add_product(db, name, concerns, ingredient_names, verified=True, category="크림"):
    p = Product(
        product_name=name, brand="브랜드", category=category,
        source_url=f"https://example.com/{name}",
        main_concerns=",".join(concerns) or None, is_concerns_verified=verified,
    )
    db.add(p)
    db.flush()
    for pos, ing_name in enumerate(ingredient_names, start=1):
        ing = db.query(Ingredient).filter(Ingredient.ingredient_name == ing_name).first()
        if ing is None:
            ing = Ingredient(ingredient_name=ing_name)
            db.add(ing)
            db.flush()
        db.add(ProductIngredient(product_id=p.id, ingredient_id=ing.id, position=pos))
    db.commit()
    return p


def save_profile(client, headers, **kw):
    body = {"skin_type": "건성", "is_sensitive": False, "concerns": [], **kw}
    res = client.post("/api/profile", json=body, headers=headers)
    assert res.status_code == 200, res.text
    return res.json()


def test_weak_password_rejected(client):
    res = client.post("/api/auth/signup", json={"email": "a@example.com", "password": "short", "nickname": "a"})
    assert res.status_code == 422


def test_protected_api_requires_token(client):
    assert client.get("/api/profile").status_code in (401, 403)
    assert client.get("/api/recommendations").status_code in (401, 403)


def test_percent_search_does_not_return_all(client, db_session):
    add_product(db_session, "수분크림", [], ["정제수"])
    add_product(db_session, "100%진정토너", [], ["정제수"])
    res = client.get("/api/products", params={"q": "%"})
    assert [p["product_name"] for p in res.json()] == ["100%진정토너"]


def test_favorite_duplicate_rejected(client, db_session, auth_headers):
    p = add_product(db_session, "수분크림", [], ["정제수"])
    assert client.post("/api/favorites", json={"product_id": p.id}, headers=auth_headers).status_code == 200
    assert client.post("/api/favorites", json={"product_id": p.id}, headers=auth_headers).status_code == 400


def test_recommendation_requires_profile(client, auth_headers):
    res = client.get("/api/recommendations", headers=auth_headers)
    assert res.status_code == 404


def test_recommendation_flow(client, db_session, auth_headers):
    add_product(db_session, "보습크림", ["건조/보습"], ["정제수", "글리세린"])
    add_product(db_session, "모공보습세럼", ["건조/보습", "모공"], ["정제수", "나이아신아마이드"])
    add_product(db_session, "향료크림", ["건조/보습", "모공"], ["정제수", "향료"])
    add_product(db_session, "초안크림", ["모공"], ["정제수"], verified=False)

    save_profile(client, auth_headers, is_sensitive=True, concerns=["건조/보습", "모공"])
    res = client.get("/api/recommendations", headers=auth_headers)
    assert res.status_code == 200, res.text
    data = res.json()

    names = [r["product_name"] for r in data["recommended"]]
    assert names == ["모공보습세럼", "보습크림"]
    assert data["recommended"][0]["match_count"] == 2
    # 민감성 + 향료 → 고민이 다 맞아도 탈락, 사유가 함께 옴
    assert data["excluded"][0]["product_name"] == "향료크림"
    assert data["excluded"][0]["reasons"][0]["type"] == "sensitive"
    assert data["skipped_unverified"] == 1

    # 개발용 옵션: 검수 전 초안 포함
    res = client.get("/api/recommendations", params={"include_unverified": True}, headers=auth_headers)
    assert "초안크림" in [r["product_name"] for r in res.json()["recommended"]]


def test_recommendation_category_and_limit(client, db_session, auth_headers):
    add_product(db_session, "크림1", ["건조/보습"], ["정제수"])
    add_product(db_session, "토너1", ["건조/보습"], ["정제수"], category="스킨/토너")
    add_product(db_session, "토너2", ["건조/보습"], ["정제수"], category="스킨/토너")
    save_profile(client, auth_headers, concerns=["건조/보습"])

    res = client.get("/api/recommendations", params={"category": "스킨/토너", "limit": 1}, headers=auth_headers)
    assert [r["product_name"] for r in res.json()["recommended"]] == ["토너1"]
