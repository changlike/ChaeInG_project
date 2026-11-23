import {API_BASE, readErrorMessage} from './config';

// 챗봇 API 요청 함수
// previousConditions: 직전 응답의 understood를 그대로 돌려보내면 서버가 후속 요청("그럼 크림으로")을 이어서 처리함
export async function sendChat(token, message, previousConditions) {
    const response = await fetch(API_BASE + '/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token,
        },
        body: JSON.stringify({message, previous_conditions: previousConditions || null}),
    });

    if (!response.ok) {
        const error = new Error(await readErrorMessage(response, '답변을 가져오지 못했어요'));
        error.status = response.status;
        throw error;
    }

    return await response.json();
}
