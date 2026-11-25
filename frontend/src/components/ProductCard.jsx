// 추천 후보 카드 (정형 데이터로만 그림)
// 순위는 매기지 않고 "후보"로 보여줌. 고민 일치 개수(점수 아님), 주력 고민 태그, 경고, "근거 보기"(근거 성분 + 설명)
import {useState} from 'react';

function ProductCard({item, evidence = [], explanation}) {
    const [open, setOpen] = useState(false);
    const r = item;

    return (
        <li className="pcard">
            <div className="pcard-rank">
                <b>추천 후보</b> · {r.category}
            </div>
            <div className="muted small">{r.brand}</div>
            <h3 className="pcard-name">{r.product_name}</h3>

            {r.total_concerns > 0 && (
                <p className="pcard-match">
                    {r.match_type === 'contained'
                        ? `주력은 아니지만 ${r.contained_matched.join(', ')} 성분이 들어 있어요`
                        : `내 고민 ${r.total_concerns}개 중 ${r.match_count}개와 맞아요`}
                </p>
            )}

            <div className="tags">
                {r.main_concerns.map((c) => (
                    <span key={c} className={r.matched_concerns.includes(c) ? 'tag tag-on' : 'tag'}>{c}</span>
                ))}
                {r.main_basis_insufficient && <span className="tag tag-warn">주력 근거 부족</span>}
                {!r.is_concerns_verified && <span className="tag tag-warn">검수 전 태그</span>}
            </div>

            {r.warnings.map((w) => (
                <p key={w.ingredient} className="small warn">
                    {w.kind === 'trace_irritant'
                        ? `⚠ ${w.ingredient}: ${w.limit_cond}`
                        : `⚠ ${w.ingredient}: 배합 한도가 있는 성분이에요 ${w.limit_cond ? `(${w.limit_cond})` : ''}`}
                </p>
            ))}

            <button className="link-button pcard-toggle" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
                근거 {open ? '접기 ▴' : '보기 →'}
            </button>
            {open && (
                <div className="pcard-evidence">
                    {explanation && <p className="small">{explanation}</p>}
                    {evidence.length > 0 ? (
                        <div className="tags">
                            {evidence.map((e) => (
                                <span key={e.ingredient} className="tag tag-evidence">
                                    {e.ingredient} · {e.concern}
                                </span>
                            ))}
                        </div>
                    ) : (
                        <p className="small muted">이 고민으로 태깅된 성분 근거가 없어요.</p>
                    )}
                    {r.preferred_hits.length > 0 && (
                        <p className="small">선호 성분 포함: {r.preferred_hits.join(', ')}</p>
                    )}
                </div>
            )}
        </li>
    );
}

export default ProductCard;
