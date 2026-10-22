import pytest
from pydantic import ValidationError

from app.schemas.user import SignupRequest


def make(password: str) -> SignupRequest:
    return SignupRequest(email="a@example.com", password=password, nickname="tester")


def test_valid_password():
    assert make("abcd1234").password == "abcd1234"


@pytest.mark.parametrize(
    "password",
    [
        "abc123",         # 8자 미만
        "abcdefgh",       # 숫자 없음
        "12345678",       # 영문 없음
        "a1" + "x" * 71,  # 72바이트 초과
        "가나다라마바사1" * 4,  # 한글은 글자당 3바이트라 글자 수가 적어도 72바이트 초과
    ],
)
def test_invalid_password(password):
    with pytest.raises(ValidationError):
        make(password)
