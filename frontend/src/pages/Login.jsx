// 로그인 페이지 컴포넌트
// 이메일, 비밀번호 입력값을 useState로 관리하고
// 로그인 버튼 클릭 시 입력값을 확인함 (아직 서버 전송은 하지 않음)
import {Link} from 'react-router-dom';
import {useState} from "react";

function Login() {
    // 메모장과, 그 메모장을 갱신하는 함수를 만듦
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    // 로그인 버튼 클릭 시 실행되는 함수
    // 지금은 콘솔에 입력값만 출력해서 확인하는 단계
    const handleLogin = () => {
        console.log('이메일:', email);
        console.log('비밀번호:', password);
    };

    return (
        <div>
            <h1>로그인 페이지</h1>
            <input
                type="text"
                placeholder="이메일 입력"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
            />
            <input
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
