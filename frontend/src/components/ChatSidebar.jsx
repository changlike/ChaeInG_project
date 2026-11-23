// 채팅 화면 왼쪽 사이드바: 브랜드, 새 상담, 내 피부 프로필 요약, 대화 목록, 보조 메뉴
import {Link, useNavigate} from 'react-router-dom';
import {clearToken} from '../auth';
import {clearChats, groupByDate} from '../chatStore';

export function Logo({size = 32}) {
    return (
        <span className="logo" style={{width: size, height: size}} aria-hidden="true">
            <svg viewBox="0 0 24 24" width={size * 0.55} height={size * 0.55} fill="none" stroke="currentColor"
                 strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 3c3.5 4.2 6 7.2 6 10.2A6 6 0 0 1 6 13.2C6 10.2 8.5 7.2 12 3z"/>
            </svg>
        </span>
    );
}

function ChatSidebar({chats, activeId, profile, onNew, onSelect, onClose}) {
    const navigate = useNavigate();
    const groups = groupByDate(chats);

    const handleLogout = () => {
        clearToken();
        clearChats();
        navigate('/login');
    };

    return (
        <aside className="chat-side">
            <div className="chat-side-top">
                <Link to="/chat" className="chat-brand"><Logo/> ChaeInG</Link>
                <button className="icon-btn side-close" onClick={onClose} aria-label="메뉴 닫기">✕</button>
            </div>

            <button className="new-chat" onClick={onNew}>＋ 새 상담</button>

            <div className="profile-card">
                <div className="profile-card-head">
                    <b>내 피부 프로필</b>
                    <Link to="/profile">{profile ? '수정' : '등록'}</Link>
                </div>
                {profile ? (
                    <>
                        <div className="tags">
                            {profile.skin_type && <span className="tag tag-on">{profile.skin_type}</span>}
                            {profile.is_sensitive && <span className="tag tag-warn">민감성</span>}
                            {(profile.concerns || []).map((c) => <span key={c} className="tag">{c}</span>)}
                        </div>
                        <p className="small muted">
                            대화에서 고민을 따로 말하지 않으면 이 프로필로 추천해요. 기피 성분과 민감성은 항상 반영돼요.
                        </p>
                    </>
                ) : (
                    <p className="small muted">프로필을 등록하면 말하지 않은 조건도 반영해서 추천해요.</p>
                )}
            </div>

            <nav className="chat-history" aria-label="대화 목록">
                {groups.length === 0 && <p className="small muted history-empty">아직 대화가 없어요.</p>}
                {groups.map((g) => (
                    <div key={g.label}>
                        <div className="history-label">{g.label}</div>
                        {g.items.map((c) => (
                            <button
                                key={c.id}
                                className={c.id === activeId ? 'history-item active' : 'history-item'}
                                onClick={() => onSelect(c.id)}
                            >
                                {c.title}
                            </button>
                        ))}
                    </div>
                ))}
            </nav>

            <div className="chat-side-bottom">
                <div className="side-links">
                    <Link to="/products">제품</Link>
                    <Link to="/ingredients">성분</Link>
                    <Link to="/favorites">찜</Link>
                    <Link to="/recommend">프로필 추천</Link>
                </div>
                <button className="link-button" onClick={handleLogout}>로그아웃</button>
            </div>
        </aside>
    );
}

export default ChatSidebar;
