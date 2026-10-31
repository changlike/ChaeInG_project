// 로그인이 필요한 페이지를 감싸는 공통 가드
// 토큰이 없으면 로그인 페이지로 보내고, 로그인 후 원래 가려던 페이지로 돌아올 수 있게 주소를 넘겨줌
import {Navigate, useLocation} from 'react-router-dom';
import {getToken} from '../auth';

function RequireAuth({children}) {
    const location = useLocation();

    if (!getToken()) {
        return <Navigate to="/login" replace state={{from: location.pathname}} />;
    }
    return children;
}

export default RequireAuth;
