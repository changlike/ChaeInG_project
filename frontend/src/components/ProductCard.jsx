// 추천 제품 카드 (정형 데이터로만 그림)
// 순위, 고민 매칭(개수만 표시, 점수 합산 아님), 주력 고민 태그, 경고, "근거 보기"(근거 성분 + 설명)
import {useState} from 'react';

function ProductCard({item, rank, evidence = [], explanation}) {
    const [open, setOpen] = useState(false);
    const r = item;
    const ratio = r.total_concerns > 0 ? Math.round((r.match_count / r.total_concerns) * 100) : 0;

    return (
        <li className="pcard">
            <div className="pcard-rank">
                <b>{rank}위</b> · {r.category}
            </div>
            <div className="muted small">{r.brand}</div>
            <h3 className="pcard-name">{r.product_name}</h3>

            {r.total_concerns > 0 && (
                <>
                    <div className="pcard-match">
                        <span>
                            {r.match_type === 'contained' ? '함유 매칭' : '고민 매칭'}
                        </span>
                        <b>
                            {r.match_type === 'contained'
                                ? `${r.contained_matched.length}/${r.total_concerns}`
                                : `${r.match_count}/${r.total_concerns}`}
                        </b>
                    </div>
                    <div className="pcard-bar" aria-hidden="true">
                        <div style={{width: `${r.match_type === 'contained' ? 0 : ratio}%`}}/>
                    </div>
                </>
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
