// 성분 검색 페이지 컴포넌트
// 성분명으로 검색하고, 클릭하면 그 성분이 들어간 제품 목록을 보여줌 (역방향 조회)
// 효능/주의사항 데이터는 아직 없어서 화면에 표시하지 않음
import {useEffect, useState} from 'react';
import {Link} from 'react-router-dom';
import {searchIngredients, getIngredientDetail} from '../api/ingredient';

function Ingredients() {
    const [searchText, setSearchText] = useState('');
    const [ingredients, setIngredients] = useState([]);
    // 지금 펼쳐서 "들어간 제품 목록"을 보여주고 있는 성분의 id
    const [expandedId, setExpandedId] = useState(null);
    const [expandedProducts, setExpandedProducts] = useState([]);

    useEffect(() => {
        searchIngredients(searchText).then(setIngredients);
    }, [searchText]);

    // 성분 하나를 클릭했을 때: 이미 펼쳐져 있으면 접고, 아니면 제품 목록을 불러와서 펼침
    const toggleExpand = async (ingredientId) => {
        if (expandedId === ingredientId) {
            setExpandedId(null);
            return;
        }

        const detail = await getIngredientDetail(ingredientId);
        setExpandedProducts(detail.products);
        setExpandedId(ingredientId);
    };

    return (
        <div>
            <h1>성분 검색</h1>

            <p>
                <Link to="/products">제품 목록</Link>
            </p>

            <input
                type="text"
                placeholder="성분명 검색"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
            />

            <ul>
                {ingredients.map((ingredient) => (
                    <li key={ingredient.id}>
                        <button onClick={() => toggleExpand(ingredient.id)}>
                            {ingredient.ingredient_name}
                        </button>

                        {expandedId === ingredient.id && (
                            <ul>
                                {expandedProducts.length === 0 && <li>이 성분이 들어간 제품이 없습니다.</li>}
                                {expandedProducts.map((product) => (
                                    <li key={product.id}>
                                        {product.brand} - {product.product_name}
                                    </li>
                                ))}
                            </ul>
                        )}
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default Ingredients;
