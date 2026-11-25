// 처음 접속했을 때 보이는 인트로 화면
// 로그인한 사용자는 App에서 바로 채팅으로 보내고, 로그인 전 사용자에게만 이 화면을 보여줌
// 안의 예시 카드는 실제 추천이 아니라 "이런 식으로 보여줘요"를 설명하는 그림임 (순위·점수 없이 고민 일치 개수와 근거 성분만 표시)
import {Link} from 'react-router-dom';
import {Logo} from '../components/ChatSidebar';

const STEPS = [
    {
        title: '말로 고민 입력',
        text: '예: "잡티에 좋은 토너, 알코올은 빼고". 프로필을 등록하면 말하지 않은 조건도 함께 반영해요.',
    },
    {
        title: '규칙으로 후보 선택',
        text: '피하는 성분이나 자극 성분이 든 제품은 먼저 거르고, 남은 제품 중 고민과 맞는 후보 3개를 골라요. 최종 선택은 직접 하세요.',
    },
    {
        title: '근거까지 확인',
        text: '왜 이 제품인지 근거 성분과, 걸러낸 제품의 이유를 함께 볼 수 있어요.',
    },
];

const CATEGORIES = ['토너', '에센스·세럼·앰플', '크림', '로션', '미스트·오일'];

function Landing() {
    const scrollToSteps = () => {
        document.getElementById('how')?.scrollIntoView({behavior: 'smooth'});
    };

    return (
        <div className="landing">
            <header className="landing-top">
                <Link to="/" className="chat-brand"><Logo/> ChaeInG</Link>
                <Link to="/login" className="landing-login">로그인</Link>
            </header>

            <section className="landing-hero">
                <div className="landing-hero-text">
                    <span className="landing-pill">성분 기반 스킨케어 추천</span>
                    <h1>내 피부에 맞는 성분,<br/>이유까지 알려드려요</h1>
                    <p>
                        피부 고민과 피하고 싶은 성분을 말해 주세요.
                        성분 기준으로 맞는 제품 후보를 고르고, 왜 골랐는지 근거와 함께 보여드려요.
                    </p>
                    <div className="landing-cta">
                        <Link to="/chat" className="landing-btn-main">상담 시작하기 →</Link>
                        <button className="landing-btn-sub" onClick={scrollToSteps}>이용 방법 보기</button>
                    </div>
                    <p className="small muted">추천은 성분 정보와 규칙으로 정한 참고용이에요.</p>
                </div>

                <div className="landing-example" aria-label="추천 화면 예시">
                    <div className="tags">
                        <span className="tag tag-on">복합성</span>
                        <span className="tag tag-warn">민감성</span>
                    </div>
                    <div className="landing-example-label">예시 화면</div>
                    <div className="pcard">
                        <div className="pcard-rank"><b>추천 후보</b> · 크림</div>
                        <h3 className="pcard-name">[제품명]</h3>
                        <p className="pcard-match">내 고민 2개 중 2개와 맞아요</p>
                        <div className="tags">
                            <span className="tag tag-on">건조/보습</span>
                            <span className="tag tag-on">홍조</span>
                        </div>
                        <div className="pcard-evidence">
                            <div className="tags">
                                <span className="tag tag-evidence">세라마이드 · 건조/보습</span>
                                <span className="tag tag-evidence">병풀추출물 · 홍조</span>
                            </div>
                            <p className="small muted">민감성이면 자극 성분이 든 제품은 먼저 걸러내요.</p>
                        </div>
                    </div>
                </div>
            </section>

            <section id="how" className="landing-how">
                <h2>세 단계면 충분해요</h2>
                <p className="muted">제품은 정해진 규칙으로 고르고, 말을 이해하는 건 챗봇이 맡아요.</p>
                <ul className="landing-steps">
                    {STEPS.map((s, i) => (
                        <li key={s.title} className="landing-step">
                            <span className="landing-step-num">{i + 1}</span>
                            <b>{s.title}</b>
                            <p className="small">{s.text}</p>
                        </li>
                    ))}
                </ul>
                <div className="landing-cats">
                    <span className="small muted">지원 카테고리</span>
                    {CATEGORIES.map((c) => <span key={c} className="chip">{c}</span>)}
                </div>
            </section>
        </div>
    );
}

export default Landing;
