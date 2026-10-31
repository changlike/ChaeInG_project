// 로그인 토큰 관리 (페이지마다 localStorage를 직접 다루지 않도록 한 곳에 모음)
const TOKEN_KEY = 'token';

export function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}
