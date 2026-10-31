// 상단 공통 네비게이션 (모든 페이지에서 같은 메뉴 + 로그인/로그아웃)
import {NavLink, useNavigate, useLocation} from 'react-router-dom';
import {getToken, clearToken} from '../auth';

function NavBar() {
    const navigate = useNavigate();
    // 페이지가 바뀔 때마다 다시 그려서 로그인 상태를 최신으로 반영
    useLocation();
    const loggedIn = Boolean(getToken());

    const handleLogout = () => {
        clearToken();
        navigate('/login');
    };

    return (
        <nav className="navbar">
            <NavLink to="/recommend" className="brand">ChaeInG</NavLink>
            <div className="nav-links">
                <NavLink to="/recommend">추천</NavLink>
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
