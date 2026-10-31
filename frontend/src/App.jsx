// 앱의 최상위 컴포넌트
// 주소(URL)에 따라 어떤 페이지를 보여줄지 라우팅 규칙을 정의함
// 로그인이 필요한 페이지는 RequireAuth로 감싸서 한 곳에서 확인함
import {BrowserRouter, Routes, Route, Navigate} from 'react-router-dom';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Profile from './pages/Profile';
import Products from './pages/Products';
import Favorites from './pages/Favorites';
import Ingredients from './pages/Ingredients';
import Recommend from './pages/Recommend';
import NavBar from './components/NavBar';
import RequireAuth from './components/RequireAuth';
import {getToken} from './auth';

function App() {
    return (
        <BrowserRouter>
            <NavBar />
            <main>
                <Routes>
                    <Route path="/" element={<Navigate to={getToken() ? '/recommend' : '/login'} replace />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/signup" element={<Signup />} />
                    <Route path="/products" element={<Products />} />
                    <Route path="/ingredients" element={<Ingredients />} />
                    <Route path="/profile" element={<RequireAuth><Profile /></RequireAuth>} />
                    <Route path="/favorites" element={<RequireAuth><Favorites /></RequireAuth>} />
                    <Route path="/recommend" element={<RequireAuth><Recommend /></RequireAuth>} />
                </Routes>
            </main>
        </BrowserRouter>
    );
}
export default App;
