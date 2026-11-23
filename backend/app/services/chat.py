# 챗봇 한 번의 요청 처리 (해석 → 병합 → 규칙 엔진 → 설명)
# 순서와 역할은 docs/llm-design.md. LLM은 해석에만 쓰고, 추천 판단은 recommender.py(규칙)가 한다.
# MVP에서는 설명 문장을 LLM 없이 템플릿으로 만든다 (엔진이 준 값만 사용하므로 근거 밖 말이 나올 수 없음)
from typing import Callable

from sqlalchemy.orm import Session

from app.services.llm.client import chat_json
from app.services.llm.interpreter import (
    INTENT_OUT_OF_SCOPE, build_confirmation, interpret, merge_with_profile,
)

TOP_N = 3
OUT_OF_SCOPE_REPLY = "저는 스킨케어 제품 추천만 도와드릴 수 있어요. 예: \"잡티에 좋은 토너 추천해줘, 알코올은 빼고\""
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
            "recommendations": [], "explanations": [], "excluded": [], "notices": notices}

    if conditions["intent"] == INTENT_OUT_OF_SCOPE:
        return {**base, "reply": OUT_OF_SCOPE_REPLY}

    engine_profile, source = merge_with_profile(conditions, profile)
    base["confirmation"] = build_confirmation(engine_profile, conditions["category"], source["concerns"])
    if not engine_profile["concerns"]:
        return {**base, "reply": NEED_CONCERN_REPLY, "needs_input": True}

    result = run_recommendation(db, engine_profile, conditions["category"])
    top = result["recommended"][:TOP_N]
    if top and not any(r["match_type"] == "main" for r in top):
        base["notices"].append(_no_main_notice(db, engine_profile, conditions["category"], run_recommendation))
    return {
        **base,
        "recommendations": top,
        "explanations": [{"product_id": r["id"], "text": template_explanation(r)} for r in top],
        "excluded": result["excluded"],
        "reply": None if top else "조건에 맞는 제품이 없어요. 제외 성분이나 카테고리를 줄여 보세요.",
    }
