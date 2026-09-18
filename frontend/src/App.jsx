// 앱의 최상위 컴포넌트
// 주소(URL)에 따라 어떤 페이지를 보여줄지 라우팅 규칙을 정의함
import {BrowserRouter, Routes, Route} from 'react-router-dom';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Profile from './pages/Profile';
import Products from './pages/Products';
import Favorites from './pages/Favorites';
import Ingredients from './pages/Ingredients';

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Login />} />
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<Signup />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/products" element={<Products />} />
                <Route path="/favorites" element={<Favorites />} />
                <Route path="/ingredients" element={<Ingredients />} />
            </Routes>
        </BrowserRouter>
    );
}
export default App;