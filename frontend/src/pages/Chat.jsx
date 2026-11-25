// 채팅 화면 (메인)
// 왼쪽 사이드바(새 상담·프로필·대화 목록) + 가운데 대화 + 아래 입력창 구성
// 사용자가 문장으로 요청하면 서버가 해석 → 규칙 엔진으로 상위 3개를 골라 돌려줌
// 화면은 서버가 준 정형 데이터(확인 문구, 카드, 근거, 탈락 사유)만 그리고, 추천 판단은 하지 않음
import {useEffect, useRef, useState} from 'react';
import {Link, useNavigate} from 'react-router-dom';
import {sendChat} from '../api/chat';
import {getProfile} from '../api/profile';
import ProductCard from '../components/ProductCard';
import ChatSidebar, {Logo} from '../components/ChatSidebar';
import {getToken, clearToken} from '../auth';
import {createChat, loadChats, saveChats} from '../chatStore';

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

function Chat() {
    const navigate = useNavigate();
    const [chats, setChats] = useState(loadChats);
    const [activeId, setActiveId] = useState(null);   // null = 아직 시작 전인 새 상담
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [profile, setProfile] = useState(null);
    const [sideOpen, setSideOpen] = useState(false);  // 좁은 화면에서만 쓰는 사이드바 열림 상태
    const bottomRef = useRef(null);

    const active = chats.find((c) => c.id === activeId) || null;
    const messages = active ? active.messages : [];

    useEffect(() => {
        getProfile(getToken()).then(setProfile).catch(() => setProfile(null));
    }, []);

    useEffect(() => {
        saveChats(chats);
    }, [chats]);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({behavior: 'smooth'});
    }, [messages.length, loading]);

    // 대화 하나를 고쳐서 목록 맨 앞(최근)으로 올림
    const updateChat = (id, change) => {
        setChats((prev) => {
            const target = prev.find((c) => c.id === id);
            if (!target) return prev;
            return [{...change(target), updatedAt: Date.now()}, ...prev.filter((c) => c.id !== id)];
        });
    };

    const send = async (text) => {
        const message = text.trim();
        if (!message || loading) return;
        setInput('');

        // 새 상담이면 이 메시지로 대화를 만듦 (제목 = 첫 메시지 앞부분)
        let id = activeId;
        let previous = active ? active.understood : null;
        if (!active) {
            const chat = {...createChat(), title: message.length > 24 ? message.slice(0, 24) + '…' : message};
            id = chat.id;
            previous = null;
            setChats((prev) => [chat, ...prev]);
            setActiveId(id);
        }
        updateChat(id, (c) => ({...c, messages: [...c.messages, {role: 'user', text: message}]}));

        setLoading(true);
        try {
            const data = await sendChat(getToken(), message, previous);
            updateChat(id, (c) => ({...c, understood: data.understood, messages: [...c.messages, {role: 'bot', data}]}));
        } catch (e) {
            if (e.status === 401 || e.status === 403) {
                clearToken();
                navigate('/login', {state: {from: '/chat'}});
                return;
            }
            updateChat(id, (c) => ({...c, messages: [...c.messages, {role: 'bot', text: e.message}]}));
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        send(input);
    };

    // Enter = 보내기, Shift+Enter = 줄바꿈 (한글 조합 중 Enter는 무시)
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
            e.preventDefault();
            send(input);
        }
    };

    const startNew = () => {
        setActiveId(null);
        setSideOpen(false);
    };

    const selectChat = (id) => {
        setActiveId(id);
        setSideOpen(false);
    };

    const u = active?.understood;

    return (
        <div className={sideOpen ? 'chat-app side-open' : 'chat-app'}>
            <ChatSidebar
                chats={chats}
                activeId={activeId}
                profile={profile}
                onNew={startNew}
                onSelect={selectChat}
                onClose={() => setSideOpen(false)}
            />
            {sideOpen && <div className="side-backdrop" onClick={() => setSideOpen(false)}/>}

            <section className="chat-main">
                <header className="chat-top">
                    <button className="icon-btn menu-btn" onClick={() => setSideOpen(true)} aria-label="메뉴 열기">☰</button>
                    <div className="chat-top-title">
                        <b>{active ? active.title : '새 상담'}</b>
                        {profile && (
                            <span className="muted small">
                                {[profile.skin_type, profile.is_sensitive ? '민감성' : null].filter(Boolean).join(' · ')} 기준
                            </span>
                        )}
                    </div>
                    <Link to="/favorites" className="top-link">♡<span className="top-link-label"> 찜한 제품</span></Link>
                </header>

                <div className="chat-scroll">
                    <div className="chat-col">
                        {messages.length === 0 && (
                            <div className="chat-welcome">
                                <Logo size={48}/>
                                <h1>어떤 피부 고민이 있으세요?</h1>
                                <p className="muted">
                                    고민과 피하고 싶은 성분을 말해 주세요. 성분 기반 규칙으로 맞는 후보 3개를 골라 근거와 함께 보여드려요.
                                </p>
                                <div className="chat-examples">
                                    {EXAMPLES.map((ex) => (
                                        <button key={ex} className="chip" onClick={() => send(ex)}>{ex}</button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {messages.map((m, i) => (
                            <div key={i} className={m.role === 'user' ? 'msg msg-user' : 'msg msg-bot'}>
                                {m.role === 'user' && <div className="bubble-user">{m.text}</div>}
                                {m.role === 'bot' && (
                                    <>
                                        <span className="msg-avatar"><Logo size={30}/></span>
                                        <div className="msg-body">
                                            {m.text && <p>{m.text}</p>}
                                            {m.data && <BotReply data={m.data}/>}
                                        </div>
                                    </>
                                )}
                            </div>
                        ))}

                        {loading && (
                            <div className="msg msg-bot">
                                <span className="msg-avatar"><Logo size={30}/></span>
                                <div className="msg-body muted">생각하는 중...</div>
                            </div>
                        )}
                        <div ref={bottomRef}/>
                    </div>
                </div>

                <form className="chat-input" onSubmit={handleSubmit}>
                    <div className="chat-input-box">
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="피부 고민이나 피하고 싶은 성분을 말해 주세요"
                            rows={2}
                            maxLength={500}
                        />
                        <button type="submit" className="send-btn" disabled={loading || !input.trim()} aria-label="보내기">↑</button>
                    </div>
                    <p className="chat-disclaimer">
                        고민과 맞는 후보를 성분 규칙으로 골라 보여드려요. 최종 선택은 직접 해 주세요. 피부 반응은 사람마다 다를 수 있습니다.
                        {u && u.avoided.length > 0 && ' 제외 성분은 대화 중 계속 유지돼요. 바꾸려면 새 상담을 시작하세요.'}
                    </p>
                </form>
            </section>
        </div>
    );
}

// 봇 응답 한 건: 확인 문구 → 안내 → 카드 3개(근거 보기 포함) → 걸러낸 제품
function BotReply({data}) {
    const [showExcluded, setShowExcluded] = useState(false);
    const explanationOf = (id) => data.explanations.find((x) => x.product_id === id)?.text;
    const evidenceOf = (id) => data.evidence.find((x) => x.product_id === id)?.items || [];

    return (
        <div className="bot-reply">
            {data.confirmation && <p className="confirm-text">{data.confirmation}</p>}
            {data.reply && <p>{data.reply}</p>}
            {data.notices.map((n, i) => <p key={i} className="notice">{n}</p>)}

            {data.recommendations.length > 0 && (
                <ul className="pcard-grid">
                    {data.recommendations.map((r) => (
                        <ProductCard
                            key={r.id}
                            item={r}
                            evidence={evidenceOf(r.id)}
                            explanation={explanationOf(r.id)}
                        />
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
