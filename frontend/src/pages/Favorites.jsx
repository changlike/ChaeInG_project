// 내 찜 목록 페이지 컴포넌트
// 로그인한 유저만 접근 가능 (토큰 없으면 로그인 페이지로 이동)
import {useEffect, useState} from 'react';
import {useNavigate, Link} from 'react-router-dom';
import {getFavorites, removeFavorite} from '../api/favorite';

function Favorites() {
    const navigate = useNavigate();
    const [favorites, setFavorites] = useState([]);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            navigate('/login');
            return;
        }

        getFavorites(token).then(setFavorites);
    }, [navigate]);

    // 찜 취소 버튼 클릭 시 실행되는 함수
    const handleRemove = async (productId) => {
        const token = localStorage.getItem('token');
        await removeFavorite(token, productId);
        setFavorites((prev) => prev.filter((f) => f.product.id !== productId));
    };

    return (
        <div>
            <h1>내 찜 목록</h1>

            <p>
                <Link to="/products">제품 목록으로</Link>
            </p>

            {favorites.length === 0 && <p>찜한 제품이 없습니다.</p>}

            <ul>
                {favorites.map((favorite) => (
                    <li key={favorite.id}>
                        {favorite.product.brand} - {favorite.product.product_name} ({favorite.product.category})
                        <button onClick={() => handleRemove(favorite.product.id)}>찜 취소</button>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default Favorites;
