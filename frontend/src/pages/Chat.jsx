// 채팅 화면 (메인)
// 사용자가 문장으로 요청하면 서버가 해석 → 규칙 엔진으로 상위 3개를 골라 돌려줌
// 화면은 서버가 준 정형 데이터(확인 문구, 카드, 탈락 사유)만 그리고, 추천 판단은 하지 않음
import {useEffect, useRef, useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {sendChat} from '../api/chat';
import ProductCard from '../components/ProductCard';
import {getToken, clearToken} from '../auth';

// 탈락 사유 종류별 표시 문구 (백엔드 recommender.py의 REASON_* 값과 같아야 함)
const REASON_LABELS = {
    sensitive: '민감성 피부 주의 성분',
    banned: '사용 금지 성분',
    avoided: '내가 피하는 성분',
};

const EXAMPLES = [
    '잡티에 좋은 토너 추천해줘, 근데 알코올은 빼고',
    '건조하고 홍조가 있는데 크림 추천해줘',
    '여드름 트러블에 좋은 세럼',
];

const WELCOME = {
    role: 'bot',
    text: '안녕하세요! 피부 고민과 피하고 싶은 성분을 말해 주세요. 성분 기반 규칙으로 상위 3개를 골라 근거와 함께 보여드려요.',
};

function Chat() {
    const navigate = useNavigate();
    const [messages, setMessages] = useState([WELCOME]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    // 직전 응답의 understood: 다음 요청에 그대로 돌려보내 후속 요청("그럼 크림으로")을 이어감
    const [understood, setUnderstood] = useState(null);
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({behavior: 'smooth'});
    }, [messages, loading]);

    const send = async (text) => {
        const message = text.trim();
        if (!message || loading) return;
        setInput('');
        setMessages((prev) => [...prev, {role: 'user', text: message}]);
        setLoading(true);
        try {
            const data = await sendChat(getToken(), message, understood);
            setUnderstood(data.understood);
            setMessages((prev) => [...prev, {role: 'bot', data}]);
        } catch (e) {
            if (e.status === 401 || e.status === 403) {
                clearToken();
                navigate('/login', {state: {from: '/chat'}});
                return;
            }
            setMessages((prev) => [...prev, {role: 'bot', text: e.message}]);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        send(input);
    };

    const reset = () => {
        setMessages([WELCOME]);
        setUnderstood(null);
    };

    return (
        <div className="page chat-page">
            <div className="chat-header">
                <h1>ChaeInG 채팅</h1>
                <button className="link-button" onClick={reset}>새 대화</button>
            </div>

            <div className="chat-log">
                {messages.map((m, i) => (
                    <div key={i} className={m.role === 'user' ? 'chat-row chat-user' : 'chat-row chat-bot'}>
                        {m.role === 'user' && <div className="bubble bubble-user">{m.text}</div>}
                        {m.role === 'bot' && m.text && <div className="bubble">{m.text}</div>}
                        {m.role === 'bot' && m.data && <BotReply data={m.data}/>}
                    </div>
                ))}
                {loading && <div className="chat-row chat-bot"><div className="bubble muted">생각하는 중...</div></div>}
                <div ref={bottomRef}/>
            </div>

            {messages.length === 1 && (
                <div className="chat-examples">
                    {EXAMPLES.map((ex) => (
                        <button key={ex} className="chip" onClick={() => send(ex)}>{ex}</button>
                    ))}
                </div>
            )}

            <form className="chat-form" onSubmit={handleSubmit}>
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="예: 잡티에 좋은 토너 추천해줘, 알코올은 빼고"
                    maxLength={500}
                />
                <button type="submit" disabled={loading || !input.trim()}>보내기</button>
            </form>
        </div>
    );
}

// 봇 응답 한 건: 확인 문구 → 안내 → 카드 3개(설명 포함) → 알림 → 걸러낸 제품
function BotReply({data}) {
    const [showExcluded, setShowExcluded] = useState(false);
    const explanationOf = (id) => data.explanations.find((x) => x.product_id === id)?.text;

    return (
        <div className="bot-reply">
            {data.confirmation && <div className="bubble confirm">{data.confirmation}</div>}
            {data.reply && <div className="bubble">{data.reply}</div>}
            {data.notices.map((n, i) => <p key={i} className="notice">{n}</p>)}

            {data.recommendations.length > 0 && (
                <ul className="card-list">
                    {data.recommendations.map((r) => (
                        <ProductCard key={r.id} item={r} explanation={explanationOf(r.id)}/>
                    ))}
                </ul>
            )}

            {data.excluded.length > 0 && (
                <section className="excluded">
                    <button className="link-button" onClick={() => setShowExcluded((v) => !v)}>
                        {showExcluded ? '▾' : '▸'} 걸러낸 제품 {data.excluded.length}개와 이유 보기
                    </button>
                    {showExcluded && (
                        <ul className="card-list">
                            {data.excluded.map((x) => (
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
        </div>
    );
}

export default Chat;
