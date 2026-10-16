# LIKE 검색에서 특수문자(%, _)를 일반 글자로 취급하게 만드는 도구
# 이스케이프하지 않으면 사용자가 "%"만 입력해도 전체가 매칭되고, "_"는 아무 한 글자와 매칭됨
LIKE_ESCAPE_CHAR = "\\"


def escape_like(keyword: str) -> str:
    # 이스케이프 문자 자신을 가장 먼저 처리해야 뒤에서 추가한 백슬래시가 중복 처리되지 않음
    return (
        keyword
        .replace(LIKE_ESCAPE_CHAR, LIKE_ESCAPE_CHAR * 2)
        .replace("%", LIKE_ESCAPE_CHAR + "%")
        .replace("_", LIKE_ESCAPE_CHAR + "_")
    )
