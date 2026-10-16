# 올리브영 "성분보기"에서 옮겨 적은 전성분 문자열을 성분 목록으로 나누는 도구
# 단순히 쉼표로 자르면 "1,2-헥산다이올"이 "1"과 "2-헥산다이올"로 쪼개지므로 규칙이 필요함
import re
from urllib.parse import urlparse, parse_qs

# 성분명 끝에 붙은 함량 표기 예: 하이알루로닉애씨드(1,000ppm), 나이아신아마이드(2%)
_AMOUNT_SUFFIX = re.compile(r"\(\s*([\d.,]+\s*(?:ppm|ppb|%))\s*\)\s*$", re.IGNORECASE)

MAX_NAME_LENGTH = 100


def split_ingredients(text: str) -> list[str]:
    """전성분 문자열을 성분 문자열 목록으로 나눔 (순서 유지).

    쉼표를 구분자로 보지 않는 경우:
      1) 괄호 안의 쉼표        예: (1,000ppm)
      2) 앞뒤가 모두 숫자인 쉼표 예: 1,2-헥산다이올
    """
    parts, buf, depth = [], [], 0
    for i, ch in enumerate(text):
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(depth - 1, 0)

        if ch == "," and depth == 0:
            prev_is_digit = i > 0 and text[i - 1].isdigit()
            next_is_digit = i + 1 < len(text) and text[i + 1].isdigit()
            if not (prev_is_digit and next_is_digit):
                parts.append("".join(buf))
                buf = []
                continue
        buf.append(ch)
    parts.append("".join(buf))

    cleaned = [re.sub(r"\s+", " ", p).strip() for p in parts]
    cleaned = [p for p in cleaned if p]

    # 쉼표 없이 공백으로만 나열된 성분표 (일부 제품이 이렇게 표기됨)
    # 쉼표로 나눴을 때 한 덩어리뿐이고 공백이 있으면 공백을 구분자로 봄
    if len(cleaned) == 1 and " " in cleaned[0]:
        return cleaned[0].split(" ")
    return cleaned


def review_reason(text: str) -> str | None:
    """자동 분리가 위험한 성분표를 걸러냄. 사유를 돌려주고, 문제가 없으면 None.
    - [ ] : 한 제품에 여러 처방(세트/기획)이 함께 적힌 경우
    - :   : 성분 목록 사이에 설명/주석이 섞인 경우
    """
    if "[" in text or "]" in text:
        return "여러 처방(세트) 표기가 섞여 있음"
    if ":" in text:
        return "성분 목록 사이에 주석/설명이 섞여 있음"
    return None


def extract_amount(raw: str) -> tuple[str, str | None]:
    """성분 문자열에서 끝의 함량 표기를 분리함. (성분명, 함량표기 또는 None)"""
    match = _AMOUNT_SUFFIX.search(raw)
    if not match:
        return raw, None
    name = raw[: match.start()].strip()
    # 이름이 비어 버리면 분리하지 않음
    if not name:
        return raw, None
    return name, match.group(1).replace(" ", "")


def parse_ingredients(text: str) -> list[dict]:
    """[{position, name, amount_note}] 형태로 반환. 같은 성분이 반복되면 처음 것만 남김."""
    result, seen = [], set()
    for raw in split_ingredients(text):
        # 유기농 표시 등의 별표(*)는 성분명에서 제거
        raw = raw.replace("*", "").strip()
        name, amount = extract_amount(raw)
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)
        result.append({"position": len(result) + 1, "name": name, "amount_note": amount})
    return result


def clean_source_url(url: str) -> str:
    """올리브영 상품 URL에서 추적용 파라미터를 제거하고 goodsNo만 남김.
    goodsNo가 없으면 (공백만 정리한) 원본을 그대로 돌려줌."""
    url = url.strip()
    parsed = urlparse(url)
    goods_no = parse_qs(parsed.query).get("goodsNo")
    if not goods_no:
        return url
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?goodsNo={goods_no[0]}"
