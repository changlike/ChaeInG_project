// 프로필 조회 API 요청 함수
// 토큰을 헤더에 실어 보내서, 로그인한 유저 본인의 프로필을 받아옴
export async function getProfile(token) {
    const response = await fetch('http://127.0.0.1:8000/api/profile', {
        headers: {
            'Authorization': 'Bearer ' + token,
        },
    });

    // 아직 등록된 프로필이 없으면(404) null을 반환 (에러 아님, 정상적인 "아직 없음" 상태)
    if (response.status === 404) {
        return null;
    }

    if (!response.ok) {
        throw new Error('프로필 조회 실패');
    }

    return await response.json();
}

// 프로필 등록/수정 API 요청 함수 (있으면 수정, 없으면 새로 생성됨)
export async function saveProfile(token, profileData) {
    const response = await fetch('http://127.0.0.1:8000/api/profile', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token,
        },
        body: JSON.stringify(profileData),
    });

    if (!response.ok) {
        throw new Error('프로필 저장 실패: 입력한 정보를 확인하세요');
    }

    return await response.json();
}
