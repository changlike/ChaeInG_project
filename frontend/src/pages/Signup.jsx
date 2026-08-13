// 회원가입 페이지 컴포넌트
// 로그인 페이지로 이동할 수 있는 링크를 포함함
import {Link} from 'react-router-dom';

function Signup() {
    return (
        <div>
            <h1>회원가입 페이지</h1>
            <p>
                이미 계정이 있으신가요? <Link to="/login">로그인</Link>
            </p>
        </div>
    );
}

export default Signup;
