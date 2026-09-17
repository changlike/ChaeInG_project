// 제품 목록 조회 API 요청 함수
// category(카테고리), q(제품명 검색어)를 선택적으로 넘길 수 있음
export async function getProducts({category, q} = {}) {
    const params = new URLSearchParams();
    if (category) params.set('category', category);
    if (q) params.set('q', q);

    const response = await fetch('http://127.0.0.1:8000/api/products?' + params.toString());

    if (!response.ok) {
        throw new Error('제품 목록 조회 실패');
    }

    return await response.json();
}
