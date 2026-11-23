# LLM 호출을 이 파일 하나에 모음 (다른 LLM으로 바꿀 때 이 파일만 고치면 됨)
# 새 패키지 없이 httpx(이미 설치됨)로 OpenAI Chat Completions를 직접 호출하고,
# 구조화 출력(json_schema, strict)으로 정해진 모양의 JSON만 받는다.
# 해석기·설명기는 이 함수를 인자로 받으므로 테스트에서는 가짜 함수로 바꿔 끼움
import json

import httpx

from app.core.config import settings

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


class LLMUnavailable(Exception):
    """키가 없거나, 호출이 실패했거나, 응답 모양이 이상할 때. 호출한 쪽은 LLM 없이 계속 진행해야 함"""


def chat_json(system: str, user: str, schema: dict, schema_name: str = "result") -> dict:
    """system/user 메시지를 보내고 schema 모양의 JSON(dict)을 돌려줌. 실패하면 LLMUnavailable"""
    if not settings.OPENAI_API_KEY:
        raise LLMUnavailable("OPENAI_API_KEY가 설정되지 않았습니다")

    payload = {
        "model": settings.OPENAI_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": schema},
        },
    }
    try:
        response = httpx.post(
            OPENAI_URL,
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json=payload,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
        # 키 값이 에러 문구에 섞이지 않도록 원인 종류만 남김
        raise LLMUnavailable(f"LLM 호출 실패 ({type(e).__name__})") from e
