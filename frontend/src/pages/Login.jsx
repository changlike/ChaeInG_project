// 로그인 페이지 컴포넌트
// 이메일, 비밀번호를 입력받아 백엔드 로그인 API를 호출함
import {Link} from 'react-router-dom';
import {useState} from "react";
import {loginUser} from '../api/auth';
import Input from '../components/Input';

function Login() {
    // 메모장과, 그 메모장을 갱신하는 함수를 만듦
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    // 로그인 버튼 클릭 시 실행되는 함수
    // 백엔드 API를 호출하고, 응답을 콘솔에서 확인함
    const handleLogin = async () => {
        try {
            const result = await loginUser(email, password);
            console.log('로그인 성공, 응답:', result);
        } catch (error) {
            console.log('로그인 실패:', error.message);
        }
    };

    return (
        <div>
            <hi>로그인 페이지</hi>
            <input
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
