// 추천 제품 카드 (정형 데이터로만 그림: 매칭 배지, 주력 고민 태그, 선호 성분, 경고)
// 추천 화면과 채팅 화면이 같이 씀. 설명 문장(explanation)은 선택으로 카드 아래에 붙임
function ProductCard({item, explanation}) {
    const r = item;
    return (
        <li className="card">
            <div className="card-head">
                <div>
                    <span className="muted">{r.brand} · {r.category}</span>
                    <h2>{r.product_name}</h2>
                </div>
                {r.total_concerns > 0 && (
                    <span className={r.match_count > 0 ? 'badge' : 'badge badge-dim'}>
                        {r.match_type === 'contained'
                            ? `주력은 아니지만 ${r.contained_matched.join(', ')} 성분이 들어 있어요`
                            : `고민 ${r.total_concerns}개 중 ${r.match_count}개 매칭`}
                    </span>
                )}
            </div>

            <div className="tags">
                {r.main_concerns.map((c) => (
                    <span key={c} className={r.matched_concerns.includes(c) ? 'tag tag-on' : 'tag'}>
                        {c}
                    </span>
                ))}
                {r.main_basis_insufficient && <span className="tag tag-warn">주력 근거 부족</span>}
                {!r.is_concerns_verified && <span className="tag tag-warn">검수 전 태그</span>}
            </div>

            {explanation && <p className="small">{explanation}</p>}
            {r.preferred_hits.length > 0 && (
                <p className="small">선호 성분 포함: {r.preferred_hits.join(', ')}</p>
            )}
            {r.warnings.map((w) => (
                <p key={w.ingredient} className="small warn">
                    {w.kind === 'trace_irritant'
                        ? `⚠ ${w.ingredient}: ${w.limit_cond}`
                        : `⚠ ${w.ingredient}: 배합 한도가 있는 성분이에요 ${w.limit_cond ? `(${w.limit_cond})` : ''}`}
                </p>
            ))}
        </li>
    );
}

export default ProductCard;
