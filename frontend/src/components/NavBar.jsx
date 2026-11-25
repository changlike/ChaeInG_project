// 상단 공통 네비게이션 (모든 페이지에서 같은 메뉴 + 로그인/로그아웃)
import {NavLink, useNavigate, useLocation} from 'react-router-dom';
import {getToken, clearToken} from '../auth';
import {clearChats} from '../chatStore';

function NavBar() {
    const navigate = useNavigate();
    // 페이지가 바뀔 때마다 다시 그려서 로그인 상태를 최신으로 반영
    const {pathname} = useLocation();
    const loggedIn = Boolean(getToken());

    const handleLogout = () => {
        clearToken();
        clearChats();
        navigate('/login');
    };

    // 채팅 화면은 자기 사이드바가, 인트로 화면은 자기 상단바가 있어서 공통 상단 메뉴를 숨김
    if (pathname === '/chat' || pathname === '/') return null;

    return (
        <nav className="navbar">
            <NavLink to="/chat" className="brand">ChaeInG</NavLink>
            <div className="nav-links">
                <NavLink to="/chat">채팅</NavLink>
                <NavLink to="/recommend">프로필 추천</NavLink>
                <NavLink to="/products">제품</NavLink>
                <NavLink to="/ingredients">성분</NavLink>
                {loggedIn && <NavLink to="/favorites">찜</NavLink>}
                {loggedIn && <NavLink to="/profile">내 프로필</NavLink>}
                {loggedIn
                    ? <button className="link-button" onClick={handleLogout}>로그아웃</button>
                    : <NavLink to="/login">로그인</NavLink>}
            </div>
        </nav>
    );
}

export default NavBar;
