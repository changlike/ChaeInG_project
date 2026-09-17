// 내 찜 목록 조회 API 요청 함수
export async function getFavorites(token) {
    const response = await fetch('http://127.0.0.1:8000/api/favorites', {
        headers: {
            'Authorization': 'Bearer ' + token,
        },
    });

    if (!response.ok) {
        throw new Error('찜 목록 조회 실패');
    }

    return await response.json();
}

// 찜하기 API 요청 함수
export async function addFavorite(token, productId) {
    const response = await fetch('http://127.0.0.1:8000/api/favorites', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token,
        },
        body: JSON.stringify({product_id: productId}),
    });

    if (!response.ok) {
        throw new Error('찜하기 실패');
    }

    return await response.json();
}

// 찜 취소 API 요청 함수
export async function removeFavorite(token, productId) {
    const response = await fetch('http://127.0.0.1:8000/api/favorites/' + productId, {
        method: 'DELETE',
        headers: {
            'Authorization': 'Bearer ' + token,
        },
    });

    if (!response.ok) {
        throw new Error('찜 취소 실패');
    }
}
