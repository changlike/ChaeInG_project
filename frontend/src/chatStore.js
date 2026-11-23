// 채팅 대화 기록 저장 (이 브라우저의 localStorage에만 저장, 서버에는 저장하지 않음)
// 저장소를 못 쓰는 환경(시크릿 창 등)에서도 화면은 동작해야 하므로 모든 읽기·쓰기를 try/catch로 감쌈
const KEY = 'chaeing_chats_v1';
const MAX_CHATS = 30;

export function loadChats() {
    try {
        const list = JSON.parse(localStorage.getItem(KEY) || '[]');
        return Array.isArray(list) ? list : [];
    } catch {
        return [];
    }
}

export function saveChats(chats) {
    try {
        // 메시지가 있는 대화만, 최근 순으로 최대 개수까지 저장
        const kept = chats.filter((c) => c.messages.length > 0).slice(0, MAX_CHATS);
        localStorage.setItem(KEY, JSON.stringify(kept));
    } catch {
        // 저장 실패는 무시 (이번 접속 동안은 화면 상태로 계속 동작)
    }
}

// 로그아웃할 때 지움 (같은 브라우저를 다른 사람이 쓸 때 대화가 보이지 않도록)
export function clearChats() {
    try {
        localStorage.removeItem(KEY);
    } catch {
        // 무시
    }
}

export function createChat() {
    return {id: String(Date.now()), title: '새 상담', messages: [], understood: null, updatedAt: Date.now()};
}

// 사이드바 목록용: 오늘 / 지난 7일 / 이전으로 묶음
export function groupByDate(chats, now = Date.now()) {
    const day = 24 * 60 * 60 * 1000;
    const startOfToday = new Date(now).setHours(0, 0, 0, 0);
    const groups = [
        {label: '오늘', items: []},
        {label: '지난 7일', items: []},
        {label: '이전', items: []},
    ];
    for (const chat of chats) {
        if (chat.updatedAt >= startOfToday) groups[0].items.push(chat);
        else if (chat.updatedAt >= startOfToday - 7 * day) groups[1].items.push(chat);
        else groups[2].items.push(chat);
    }
    return groups.filter((g) => g.items.length > 0);
}
