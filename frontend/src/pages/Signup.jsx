// 회원가입 페이지 컴포넌트
// useState로 이메일/비밀번호/닉네임 입력값을 관리하고, Input 컴포넌트로 입력창을 구성함
// 버튼 클릭 시 백엔드 회원가입 API를 호출함

// react-router-dom에서 페이지 이동용 Link 컴포넌트와, 코드로 페이지를 이동시키는 useNavigate를 가져옴
import {Link, useNavigate} from 'react-router-dom';
// react에서 상태 관리 기능인 useState를 가져옴
import {useState} from 'react';
// 회원가입 API 요청 함수를 가져옴
import {signupUser} from '../api/auth';
// 재사용 가능한 입력창 컴포넌트를 가져옴
import Input from '../components/Input';

// 회원가입 페이지를 구성하는 컴포넌트 함수
function Signup() {
    // 이메일 입력값을 저장하는 상태(email)와 갱신 함수(setEmail), 초기값은 빈 문자열
    const [email, setEmail] = useState('');
    // 비밀번호 입력값을 저장하는 상태(password)와 갱신 함수(setPassword), 초기값은 빈 문자열
    const [password, setPassword] = useState('');
    // 닉네임 입력값을 저장하는 상태(nickname)와 갱신 함수(setNickname), 초기값은 빈 문자열
    const [nickname, setNickname] = useState('');
    // 회원가입 성공 후 로그인 페이지로 이동시키기 위한 함수
    const navigate = useNavigate();

    // 회원가입 버튼 클릭 시 실행되는 함수
    // 백엔드 API를 호출하고, 성공하면 로그인 페이지로 이동시킴
    const handleSignup = async () => {
        try {
            const result = await signupUser(email, password, nickname);
            console.log('회원가입 성공, 응답:', result);
            alert('회원가입이 완료되었습니다. 로그인해주세요.');
            navigate('/login');
        } catch (error) {
            console.log('회원가입 실패:', error.message);
        }
    };

    // 실제로 화면에 그려질 내용을 반환
    return (
        <div>
            {/* 페이지 제목 */}
            <h1>회원가입 페이지</h1>

            {/* 이메일 입력창: type="text"로 일반 텍스트 입력 */}
            {/* value={email}로 현재 email 상태값을 입력창에 표시 */}
            {/* onChange로 타이핑할 때마다 email 상태를 갱신 */}
            <Input
                type="text"
                placeholder="이메일 입력"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
            />

            {/* 비밀번호 입력창: type="password"로 입력값이 화면에 노출되지 않게 함 */}
            <Input
                type="password"
                placeholder="비밀번호 입력"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
            />

            {/* 닉네임 입력창 */}
            <Input
                type="text"
                placeholder="닉네임 입력"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
            />

            <button onClick={handleSignup}>회원가입</button>

            <p>
                이미 계정이 있으신가요? <Link to="/login">로그인</Link>
            </p>
        </div>
    );
}

export default Signup;
