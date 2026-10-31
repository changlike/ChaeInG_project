// 내 찜 목록 페이지 컴포넌트
// 로그인한 유저만 접근 가능 (App.jsx의 RequireAuth가 확인)
import {useEffect, useState} from 'react';
import {getFavorites, removeFavorite} from '../api/favorite';
import {getToken} from '../auth';

function Favorites() {
    const [favorites, setFavorites] = useState([]);

    useEffect(() => {
        getFavorites(getToken()).then(setFavorites);
    }, []);

    // 찜 취소 버튼 클릭 시 실행되는 함수
    const handleRemove = async (productId) => {
        await removeFavorite(getToken(), productId);
        setFavorites((prev) => prev.filter((f) => f.product.id !== productId));
    };

    return (
        <div className="page">
            <h1>내 찜 목록</h1>

            {favorites.length === 0 && <p>찜한 제품이 없습니다.</p>}

            <ul className="card-list">
                {favorites.map((favorite) => (
                    <li key={favorite.id} className="card card-row">
                        <div>
                            <span className="muted small">{favorite.product.brand} · {favorite.product.category}</span>
                            <h2>{favorite.product.product_name}</h2>
                        </div>
                        <button
                            className="heart"
                            aria-pressed={true}
                            aria-label="찜 취소"
                            onClick={() => handleRemove(favorite.product.id)}
                        >
                            ♥
                        </button>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default Favorites;
