// 제품 목록/검색 페이지 컴포넌트
// 로그인 없이도 볼 수 있음. 찜하기는 로그인한 사람만 가능(토큰 없으면 로그인 페이지로 이동)
import {useEffect, useState} from 'react';
import {useNavigate, Link} from 'react-router-dom';
import {getProducts} from '../api/product';
import {getFavorites, addFavorite, removeFavorite} from '../api/favorite';
import Input from '../components/Input';

function Products() {
    const navigate = useNavigate();

    const [products, setProducts] = useState([]);
    const [categories, setCategories] = useState([]);
    const [searchText, setSearchText] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('');
    // 지금 로그인한 유저가 찜한 제품 id들의 모음 (하트 버튼 상태 표시용)
    const [favoritedIds, setFavoritedIds] = useState(new Set());

    // 카테고리 목록은 필터 조건 없이 전체를 한 번 불러와서 뽑아냄
    useEffect(() => {
        getProducts().then((allProducts) => {
            const uniqueCategories = [...new Set(allProducts.map((p) => p.category).filter(Boolean))];
            setCategories(uniqueCategories);
        });
    }, []);

    // 로그인한 상태라면 내 찜 목록을 불러와서, 이미 찜한 제품에 하트를 채워서 보여줌
    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) return;

        getFavorites(token).then((favorites) => {
            setFavoritedIds(new Set(favorites.map((f) => f.product.id)));
        });
    }, []);

    // 검색어/카테고리가 바뀔 때마다 그 조건으로 제품 목록을 다시 불러옴
    useEffect(() => {
        getProducts({category: selectedCategory || undefined, q: searchText || undefined}).then(setProducts);
    }, [searchText, selectedCategory]);

    // 찜하기/찜취소 버튼 클릭 시 실행되는 함수
    const toggleFavorite = async (productId) => {
        const token = localStorage.getItem('token');
        if (!token) {
            navigate('/login');
            return;
        }

        if (favoritedIds.has(productId)) {
            await removeFavorite(token, productId);
            setFavoritedIds((prev) => {
                const next = new Set(prev);
                next.delete(productId);
                return next;
            });
        } else {
            await addFavorite(token, productId);
            setFavoritedIds((prev) => new Set(prev).add(productId));
        }
    };

    return (
        <div>
            <h1>제품 목록</h1>

            <p>
                <Link to="/favorites">내 찜 목록</Link> | <Link to="/ingredients">성분 검색</Link>
            </p>

            <Input
                type="text"
                placeholder="제품명 검색"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
            />

            <select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}>
                <option value="">전체 카테고리</option>
                {categories.map((category) => (
                    <option key={category} value={category}>{category}</option>
                ))}
            </select>

            <ul>
                {products.map((product) => (
                    <li key={product.id}>
                        {product.brand} - {product.product_name} ({product.category})
                        <button onClick={() => toggleFavorite(product.id)}>
                            {favoritedIds.has(product.id) ? '찜 취소' : '찜하기'}
                        </button>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default Products;
