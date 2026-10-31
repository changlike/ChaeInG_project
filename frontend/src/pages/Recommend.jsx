// 추천 결과 페이지
// 내 피부 프로필로 스코어링 엔진을 실행하고, 추천 이유(고민 매칭)와 탈락 이유(게이트)를 함께 보여줌
// 점수는 합산하지 않음: 게이트 통과 여부 → 고민 매칭 개수 → 경고 표시 순서
import {useEffect, useState} from 'react';
import {Link, useNavigate} from 'react-router-dom';
import {getRecommendations} from '../api/recommendation';
import {getProducts} from '../api/product';
import {getToken, clearToken} from '../auth';

// 탈락 사유 종류별 표시 문구 (백엔드 recommender.py의 REASON_* 값과 같아야 함)
const REASON_LABELS = {
    sensitive: '민감성 피부 주의 성분',
    banned: '사용 금지 성분',
    avoided: '내가 피하는 성분',
};

function Recommend() {
    const navigate = useNavigate();

    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const [noProfile, setNoProfile] = useState(false);
    const [categories, setCategories] = useState([]);
    const [category, setCategory] = useState('');
    const [includeUnverified, setIncludeUnverified] = useState(false);
    const [showExcluded, setShowExcluded] = useState(false);

    useEffect(() => {
        getProducts().then((all) => {
            setCategories([...new Set(all.map((p) => p.category).filter(Boolean))]);
        });
    }, []);

    useEffect(() => {
        getRecommendations(getToken(), {category, includeUnverified})
            .then((data) => {
                setResult(data);
                setError('');
                setNoProfile(false);
            })
            .catch((e) => {
                if (e.status === 401) {
                    // 토큰 만료 → 다시 로그인
                    clearToken();
                    navigate('/login', {state: {from: '/recommend'}});
                } else if (e.status === 404) {
                    setNoProfile(true);
                } else {
                    setError(e.message);
                }
            });
    }, [category, includeUnverified, navigate]);

    if (noProfile) {
        return (
            <div className="page">
                <h1>맞춤 추천</h1>
                <p>추천을 받으려면 피부 프로필이 필요해요.</p>
                <p><Link to="/profile">피부 프로필 등록하기</Link></p>
            </div>
        );
    }

    return (
        <div className="page">
            <h1>맞춤 추천</h1>
            <p className="muted">
                성분 기반 규칙으로 판단합니다. 민감성·기피 성분이 있는 제품은 먼저 걸러내고,
                남은 제품을 내 고민과 겹치는 개수가 많은 순으로 보여줘요.
            </p>

            <div className="toolbar">
                <select value={category} onChange={(e) => setCategory(e.target.value)}>
                    <option value="">전체 카테고리</option>
                    {categories.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
                <label className="checkbox">
                    <input
                        type="checkbox"
                        checked={includeUnverified}
                        onChange={(e) => setIncludeUnverified(e.target.checked)}
                    />
                    검수 전 고민 태그도 포함 (개발용)
                </label>
            </div>

            {error && <p className="error">{error}</p>}
            {!result && !error && <p>불러오는 중...</p>}

            {result && (
                <>
                    {result.skipped_unverified > 0 && !includeUnverified && (
                        <p className="notice">
                            주력 고민 검수가 끝나지 않은 제품 {result.skipped_unverified}개는 추천에서 제외했어요.
                        </p>
                    )}

                    {result.recommended.length === 0 && <p>조건에 맞는 추천 제품이 없어요.</p>}

                    <ul className="card-list">
                        {result.recommended.map((r) => (
                            <li key={r.id} className="card">
                                <div className="card-head">
                                    <div>
                                        <span className="muted">{r.brand} · {r.category}</span>
                                        <h2>{r.product_name}</h2>
                                    </div>
                                    {r.total_concerns > 0 && (
                                        <span className={r.match_count > 0 ? 'badge' : 'badge badge-dim'}>
                                            고민 {r.total_concerns}개 중 {r.match_count}개 매칭
                                        </span>
                                    )}
                                </div>

                                <div className="tags">
                                    {r.main_concerns.map((c) => (
                                        <span key={c} className={r.matched_concerns.includes(c) ? 'tag tag-on' : 'tag'}>
                                            {c}
                                        </span>
                                    ))}
                                    {!r.is_concerns_verified && <span className="tag tag-warn">검수 전 태그</span>}
                                </div>

                                {r.preferred_hits.length > 0 && (
                                    <p className="small">선호 성분 포함: {r.preferred_hits.join(', ')}</p>
                                )}
                                {r.warnings.map((w) => (
                                    <p key={w.ingredient} className="small warn">
                                        ⚠ {w.ingredient}: 배합 한도가 있는 성분이에요 {w.limit_cond && `(${w.limit_cond})`}
                                    </p>
                                ))}
                            </li>
                        ))}
                    </ul>

                    {result.excluded.length > 0 && (
                        <section className="excluded">
                            <button className="link-button" onClick={() => setShowExcluded((v) => !v)}>
                                {showExcluded ? '▾' : '▸'} 걸러낸 제품 {result.excluded.length}개와 이유 보기
                            </button>
                            {showExcluded && (
                                <ul className="card-list">
                                    {result.excluded.map((x) => (
                                        <li key={x.id} className="card card-dim">
                                            <span className="muted">{x.brand} · {x.category}</span>
                                            <h2>{x.product_name}</h2>
                                            <ul className="reasons">
                                                {x.reasons.map((reason, i) => (
                                                    <li key={i}>
                                                        <b>{REASON_LABELS[reason.type] || reason.type}</b>: {reason.ingredient}
                                                        <span className="muted"> ({reason.detail})</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </section>
                    )}
                </>
            )}
        </div>
    );
}

export default Recommend;
