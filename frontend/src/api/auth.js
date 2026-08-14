// 로그인 API 요청 함수
// 이메일, 비밀번호를 백엔드로 전송하고, 응답(JWT 토큰 등)을 반환함
export async function loginUser(email, password) {
    const response = await fetch('http://127.0.0.1:8000/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            },
        body: JSON.stringify({ email, password}),
    });

    // 응답이 실패(401 등)면 에러를 발생시킴
    if (!response.ok) {
        throw new Error('로그인 실패: 이메일 또는 비밀번호를 확인하세요');
    }

    // 성공하면 응답 데이터(JSON)를 반환함
    const data = await response.json();
    return data;
}