import {API_BASE, readErrorMessage} from './config';

// 추천 API 요청 함수 (로그인한 유저의 피부 프로필로 스코어링 엔진 실행)
// category: 카테고리 한정, includeUnverified: 주력 고민 검수 전 제품 포함(개발·데모용)
export async function getRecommendations(token, {category, includeUnverified} = {}) {
    const params = new URLSearchParams();
    if (category) params.set('category', category);
    if (includeUnverified) params.set('include_unverified', 'true');

    const response = await fetch(API_BASE + '/api/recommendations?' + params.toString(), {
        headers: {
            'Authorization': 'Bearer ' + token,
        },
    });

    if (!response.ok) {
        const error = new Error(await readErrorMessage(response, '추천 결과를 불러오지 못했습니다'));
        // 화면에서 401(로그인 만료), 404(프로필 없음)를 구분해서 처리하기 위함
        error.status = response.status;
        throw error;
    }

    return await response.json();
}
