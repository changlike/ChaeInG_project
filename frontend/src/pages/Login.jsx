// 로그인 페이지 컴포넌트
// 이메일, 비밀번호를 입력받아 백엔드 로그인 API를 호출함
import {Link, useNavigate, useLocation} from 'react-router-dom';
import {useState} from "react";
import {loginUser} from '../api/auth';
import Input from '../components/Input';
import {setToken} from '../auth';

function Login() {
    // 메모장과, 그 메모장을 갱신하는 함수를 만듦
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const navigate = useNavigate();
    // 로그인이 필요한 페이지에서 넘어왔다면, 로그인 후 그 페이지로 돌려보냄
    const location = useLocation();
    const redirectTo = location.state?.from || '/recommend';

    // 로그인 버튼 클릭 시 실행되는 함수
    // 백엔드 API를 호출하고, 받은 토큰을 저장한 뒤 원래 가려던 페이지(기본: 추천)로 이동함
    const handleLogin = async () => {
        try {
            const result = await loginUser(email, password);
            // 다른 페이지/다른 API 호출에서도 로그인 상태를 알 수 있도록 토큰을 저장해둠
            setToken(result.access_token);
            navigate(redirectTo, {replace: true});
        } catch (error) {
            setErrorMessage(error.message);
        }
    };

    return (
        <div className="page narrow">
            <h1>로그인</h1>
            {location.state?.message && <p className="notice">{location.state.message}</p>}
            <Input
                type="text"
                placeholder="이메일 입력"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
            />
            <Input
                type="password"
                placeholder="비밀번호 입력"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
            />
            <button onClick={handleLogin}>로그인</button>
            {errorMessage && <p className="error">{errorMessage}</p>}
            <p className="small muted">계정이 없으신가요?</p>
            {/* 회원가입은 보조 버튼 (스카이블루 테두리) */}
            <Link to="/signup" className="button-outline">회원가입</Link>
        </div>
    );
}

export default Login;
