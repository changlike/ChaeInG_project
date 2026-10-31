// 백엔드 주소를 한 곳에서 관리 (배포 시 VITE_API_BASE 환경변수로 바꿀 수 있음)
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

// 서버 에러 응답({"detail": ...})에서 사람이 읽을 메시지를 꺼냄
// 422(입력 검증 실패)는 detail이 배열로 오므로 첫 번째 항목의 메시지를 씀
export async function readErrorMessage(response, fallback) {
    try {
        const data = await response.json();
        if (typeof data.detail === 'string') return data.detail;
        if (Array.isArray(data.detail) && data.detail[0]?.msg) {
            return data.detail[0].msg.replace(/^Value error, /, '');
        }
    } catch {
        // JSON이 아닌 응답이면 기본 문구 사용
    }
    return fallback;
}
