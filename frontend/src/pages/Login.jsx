// 로그인 페이지 컴포넌트
// 이메일, 비밀번호를 입력받아 백엔드 로그인 API를 호출함
import {Link, useNavigate} from 'react-router-dom';
import {useState} from "react";
import {loginUser} from '../api/auth';
import Input from '../components/Input';

function Login() {
    // 메모장과, 그 메모장을 갱신하는 함수를 만듦
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();

    // 로그인 버튼 클릭 시 실행되는 함수
    // 백엔드 API를 호출하고, 받은 토큰을 localStorage에 저장한 뒤 프로필 페이지로 이동함
    const handleLogin = async () => {
        try {
            const result = await loginUser(email, password);
            // 다른 페이지/다른 API 호출에서도 로그인 상태를 알 수 있도록 토큰을 저장해둠
            localStorage.setItem('token', result.access_token);
            console.log('로그인 성공, 응답:', result);
            navigate('/profile');
        } catch (error) {
            console.log('로그인 실패:', error.message);
        }
    };

    return (
        <div>
            <h1>로그인 페이지</h1>
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
            <p>
                계정이 없으신가요? <Link to="/signup">회원가입</Link>
            </p>
        </div>
    );
}

export default Login;
