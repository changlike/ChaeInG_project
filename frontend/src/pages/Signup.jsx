// 회원가입 페이지 컴포넌트
// useState로 이메일/비밀번호 입력값을 관리하고, Input 컴포넌트로 입력창을 구성함
// 현재 회원가입 API 연동 전 단계로, 버튼 클릭 시 콘솔 출력만 수행함

// react-router-dom에서 페이지 이동용 Link 컴포넌트를 가져옴
import {Link} from 'react-router-dom';
// react에서 상태 관리 기능인 useState를 가져옴
import {useState} from 'react';
// 재사용 가능한 입력창 컴포넌트를 가져옴
import Input from '../components/Input';

// 회원가입 페이지를 구성하는 컴포넌트 함수
function Signup() {
    // 이메일 입력값을 저장하는 상태(email)와 갱신 함수(setEmail), 초기값은 빈 문자열
    const [email, setEmail] = useState('');
    // 비밀번호 입력값을 저장하는 상태(password)와 갱신 함수(setPassword), 초기값은 빈 문자열
    const [password, setPassword] = useState('');

    // 회원가입 버튼 클릭 시 실행되는 함수
    // 추후 회원가입 API(api/auth.js) 연동 시 이 함수 내부를 교체할 예정
    const handleSignup = () => {
        // 현재 email 상태값을 콘솔에 출력
        console.log('이메일:', email);
        // 현재 password 상태값을 콘솔에 출력
        console.log('비밀번호:', password);
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

            {/* 비밀번호 입력창: type*/}


            <p>
                이미 계정이 있으신가요? <Link to="/login">로그인</Link>
            </p>
        </div>
    );
}

export default Signup;
