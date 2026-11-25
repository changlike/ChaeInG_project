# 챗봇 한 번의 요청 처리 (해석 → 병합 → 규칙 엔진 → 설명)
# 순서와 역할은 docs/llm-design.md. LLM은 해석에만 쓰고, 추천 판단은 recommender.py(규칙)가 한다.
# MVP에서는 설명 문장을 LLM 없이 템플릿으로 만든다 (엔진이 준 값만 사용하므로 근거 밖 말이 나올 수 없음)
from typing import Callable

from sqlalchemy.orm import Session

from app.services.llm.client import chat_json
from app.services.llm.interpreter import (
    INTENT_GREETING, INTENT_OFF_TOPIC, INTENT_RECOMMEND, INTENT_UNSUPPORTED,
    build_confirmation, interpret, merge_with_profile,
)

TOP_N = 3

# 추천이 아닌 문장 유형별 안내 문구 (LLM이 아니라 코드의 고정 문구)
GREETING_REPLY = (
    "안녕하세요, ChaeInG입니다.\n"
    "피부 고민과 피하고 싶은 성분을 말해 주시면, 성분 기준으로 맞는 제품 후보 3개를 근거와 함께 골라 드려요. "
    "토너·에센스/세럼/앰플·로션·크림·미스트/오일 중에서 추천해 드려요.\n\n"
    "이렇게 말해 보세요\n"
    "· 잡티에 좋은 토너 추천해줘, 알코올은 빼고\n"
    "· 건조하고 홍조가 있는데 크림 추천해줘"
)
UNSUPPORTED_REPLY = (
    "그 요청은 아직 도와드리기 어려워요. 저는 피부 고민(건조, 트러블, 홍조, 잡티, 모공, 주름)과 피하고 싶은 성분으로 "
    "토너·세럼·로션·크림·미스트 중에서 추천하는 일만 해요. 선크림·클렌저 같은 다른 제품군, 성분 설명, 가격, 비건 같은 조건은 지원하지 않아요.\n"
    "예: \"잡티에 좋은 토너 추천해줘, 알코올은 빼고\""
)
INVALID_INPUT_REPLY = (
    "무슨 말씀인지 잘 이해하지 못했어요. 피부 고민이나 피하고 싶은 성분을 알려 주세요.\n"
    "예: \"속건조가 심한데 크림 추천해줘\", \"여드름이 고민이야, 향료는 빼고\""
)
NON_RECOMMEND_REPLIES = {
    INTENT_GREETING: GREETING_REPLY,
    INTENT_UNSUPPORTED: UNSUPPORTED_REPLY,
    INTENT_OFF_TOPIC: INVALID_INPUT_REPLY,
}
NEED_CONCERN_REPLY = "어떤 피부 고민이 있는지 알려 주세요. 예: 건조함, 트러블, 홍조, 잡티, 모공, 주름"

EMPTY_CONDITIONS = {"intent": "recommend", "concerns": [], "category": None, "avoided": [], "preferred": []}


def template_explanation(item: dict) -> str:
    """추천 카드 옆 설명 문장. 엔진 결과(주력 고민, 일치 고민, 선호 성분, 경고)만 사용"""
    matched = ", ".join(item["matched_concerns"])
    if item["match_type"] == "main":
        text = f"이 제품은 {matched}이(가) 주력이라 요청과 맞아요."
    elif item["match_type"] == "contained":
        text = f"주력은 아니지만 {', '.join(item['contained_matched'])} 관련 성분이 들어 있어요."
    else:
        text = "요청한 고민과 직접 맞는 근거는 부족해요."
    if item["main_basis_insufficient"]:
        text = "주력 고민 근거가 부족한 제품이에요."
    if item["preferred_hits"]:
        text += f" 선호 성분({', '.join(item['preferred_hits'])})이 들어 있어요."
    if item["warnings"]:
        text += " 주의할 성분이 있으니 아래 경고를 확인해 주세요."
    return text


MAX_EVIDENCE = 4          # 카드 하나에 보여줄 근거 성분 최대 개수
EVIDENCE_PER_CONCERN = 2  # 고민 하나당 최대 개수


def build_evidence(db: Session, top: list[dict]) -> list[dict]:
    """추천 카드의 '근거 성분': 요청한 고민 중 이 제품에서 맞은 고민과, 그 고민으로 태깅된 성분(성분표 순서대로 최대 4개)
    성분 태그표(출처가 붙은 표)에서 가져온 값이라 LLM이 지어낸 말이 아님"""
    from app.models.product import Ingredient, ProductIngredient
    from app.services.recommender import load_concern_tables

    if not top:
        return []
    tags, _ = load_concern_tables()
    rows = (
        db.query(ProductIngredient.product_id, ProductIngredient.position, Ingredient.ingredient_name)
        .join(Ingredient, Ingredient.id == ProductIngredient.ingredient_id)
        .filter(ProductIngredient.product_id.in_([r["id"] for r in top]))
        .order_by(ProductIngredient.product_id, ProductIngredient.position)
        .all()
    )
    by_product: dict[int, list[str]] = {}
    for product_id, _position, name in rows:
        by_product.setdefault(product_id, []).append(name)

    result = []
    for r in top:
        concerns = r["matched_concerns"] + r["contained_matched"]
        items = []
        # 고민마다 성분표 순서대로 앞의 몇 개씩 (보습 성분이 많은 제품에서 다른 고민의 근거가 가려지지 않도록)
        for concern in concerns:
            count = 0
            for name in by_product.get(r["id"], []):
                tag = tags.get(name)
                if tag and not tag["exclude"] and concern in tag["all"] and count < EVIDENCE_PER_CONCERN:
                    items.append({"ingredient": name, "concern": concern})
                    count += 1
        result.append({"product_id": r["id"], "items": items[:MAX_EVIDENCE]})
    return result


def _no_main_notice(db, engine_profile: dict, category: str | None, run_recommendation) -> str:
    """고른 카테고리에 주력이 맞는 제품이 없을 때의 안내. 다른 카테고리에 있으면 알려줌 (엔진 결과만 사용)"""
    concerns = ", ".join(engine_profile["concerns"])
    where = f"{category} 중에는 " if category else ""
    text = f"{where}{concerns}이(가) 주력인 제품이 없어서, 다른 조건에 가까운 제품을 보여드려요."
    if category:
        others = run_recommendation(db, engine_profile, None)["recommended"]
        categories = list(dict.fromkeys(r["category"] for r in others if r["match_type"] == "main" and r["category"]))
        if categories:
            text += f" 주력이 맞는 제품은 {', '.join(categories[:3])}에 있어요."
    return text


def run_chat(
    db: Session,
    message: str,
    previous: dict | None,
    profile: dict | None,
    llm: Callable = chat_json,
) -> dict:
    # 순환 import를 피하려고 함수 안에서 가져옴 (recommendation API가 같은 진입점을 씀)
    from app.api.recommendation import run_recommendation

    conditions, notices = interpret(message, previous, llm)
    if conditions is None:  # LLM 실패: 직전 조건이 있으면 이어서, 없으면 저장된 프로필만으로 진행
        from app.services.llm.interpreter import sanitize_previous
        conditions = sanitize_previous(previous) or dict(EMPTY_CONDITIONS)

    base = {"understood": conditions, "confirmation": "", "reply": None, "needs_input": False,
            "recommendations": [], "explanations": [], "evidence": [], "excluded": [], "notices": notices}

    # 인사·미지원 요청·무관한 말은 추천을 실행하지 않고 유형별 안내 문구만 돌려줌
    if conditions["intent"] != INTENT_RECOMMEND:
        return {**base, "reply": NON_RECOMMEND_REPLIES[conditions["intent"]]}

    engine_profile, source = merge_with_profile(conditions, profile)
    base["confirmation"] = build_confirmation(engine_profile, conditions["category"], source["concerns"])
    if not engine_profile["concerns"]:
        return {**base, "reply": NEED_CONCERN_REPLY, "needs_input": True}

    # 게이트에는 같은 물질의 다른 표기까지 넣은 목록을 씀 (예: 알코올 → 에탄올도 거름)
    gate_profile = {**engine_profile, "avoided_ingredients": engine_profile["avoided_for_gate"]}
    result = run_recommendation(db, gate_profile, conditions["category"])
    top = result["recommended"][:TOP_N]
    if top and not any(r["match_type"] == "main" for r in top):
        base["notices"].append(_no_main_notice(db, engine_profile, conditions["category"], run_recommendation))
    return {
        **base,
        "recommendations": top,
        "explanations": [{"product_id": r["id"], "text": template_explanation(r)} for r in top],
        "evidence": build_evidence(db, top),
        "excluded": result["excluded"],
        "reply": None if top else "조건에 맞는 제품이 없어요. 제외 성분이나 카테고리를 줄여 보세요.",
    }
