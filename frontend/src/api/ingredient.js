// 성분 검색 API 요청 함수
export async function searchIngredients(q) {
    const params = new URLSearchParams();
    if (q) params.set('q', q);

    const response = await fetch('http://127.0.0.1:8000/api/ingredients?' + params.toString());

    if (!response.ok) {
        throw new Error('성분 검색 실패');
    }

    return await response.json();
}

// 성분 상세 조회 API 요청 함수 (이 성분이 들어간 제품 목록 포함)
export async function getIngredientDetail(ingredientId) {
    const response = await fetch('http://127.0.0.1:8000/api/ingredients/' + ingredientId);

    if (!response.ok) {
        throw new Error('성분 상세 조회 실패');
    }

    return await response.json();
}
