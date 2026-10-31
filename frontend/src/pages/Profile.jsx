// 피부 프로필 페이지 컴포넌트
// 로그인한 유저만 접근 가능 (App.jsx의 RequireAuth가 확인)
// 스킨타입/민감성/고민/선호·기피 성분을 입력받아 백엔드에 저장함
import {useEffect, useState} from 'react';
import {Link} from 'react-router-dom';
import {getProfile, saveProfile} from '../api/profile';
import Input from '../components/Input';
import {getToken} from '../auth';

// 스킨타입 고정 목록 (피부타입 게이트는 v1 미적용이지만 값은 계속 수집함)
const SKIN_TYPES = ['건성', '지성', '복합성', '수부지', '중성'];

// 고민 고정 목록 (제품 쪽 "주력 고민" 태깅과 공유하는 어휘 - 백엔드 ALLOWED_CONCERNS와 동일해야 함)
const CONCERN_OPTIONS = ['여드름/트러블', '모공', '홍조', '건조/보습', '미백/톤', '주름/탄력'];

function Profile() {
    const [skinType, setSkinType] = useState(SKIN_TYPES[0]);
    const [isSensitive, setIsSensitive] = useState(false);
    const [concerns, setConcerns] = useState([]);
    const [preferredIngredients, setPreferredIngredients] = useState('');
    const [avoidedIngredients, setAvoidedIngredients] = useState('');
    const [savedMessage, setSavedMessage] = useState('');

    // 페이지 진입 시: 기존 프로필 있으면 불러와서 채워넣기
    useEffect(() => {
        getProfile(getToken()).then((profile) => {
            if (profile) {
                setSkinType(profile.skin_type);
                setIsSensitive(profile.is_sensitive);
                setConcerns(profile.concerns || []);
                setPreferredIngredients(profile.preferred_ingredients || '');
                setAvoidedIngredients(profile.avoided_ingredients || '');
            }
        });
    }, []);

    // 고민 체크박스 하나를 눌렀을 때 concerns 배열에 추가/제거
    const toggleConcern = (concern) => {
        setConcerns((prev) =>
            prev.includes(concern)
                ? prev.filter((c) => c !== concern)
                : [...prev, concern]
        );
    };

    // 저장 버튼 클릭 시 실행되는 함수
    const handleSave = async () => {
        try {
            await saveProfile(getToken(), {
                skin_type: skinType,
                is_sensitive: isSensitive,
                concerns: concerns,
                preferred_ingredients: preferredIngredients || null,
                avoided_ingredients: avoidedIngredients || null,
            });
            setSavedMessage('저장됐습니다.');
        } catch (error) {
            setSavedMessage(error.message);
        }
    };

    return (
        <div className="page narrow">
            <h1>내 피부 프로필</h1>

            <div className="field">
                <label className="field-label">피부타입</label>
                <select value={skinType} onChange={(e) => setSkinType(e.target.value)}>
                    {SKIN_TYPES.map((type) => (
                        <option key={type} value={type}>{type}</option>
                    ))}
                </select>
            </div>

            <div className="field">
                <label>
                    <input
                        type="checkbox"
                        checked={isSensitive}
                        onChange={(e) => setIsSensitive(e.target.checked)}
                    />
                    민감성 피부예요
                </label>
            </div>

            {/* 고민은 체크박스 대신 눌러서 켜고 끄는 태그로 선택 (design-system.md 와이어프레임) */}
            <div className="field">
                <span className="field-label">고민 (해당하는 것 모두 선택)</span>
                {CONCERN_OPTIONS.map((concern) => (
                    <button
                        key={concern}
                        type="button"
                        className="tag-toggle"
                        aria-pressed={concerns.includes(concern)}
                        onClick={() => toggleConcern(concern)}
                    >
                        {concern}
                    </button>
                ))}
            </div>

            <span className="field-label">선호 / 기피 성분 (콤마로 구분)</span>
            <Input
                type="text"
                placeholder="선호 성분 (예: 나이아신아마이드, 히알루론산)"
                value={preferredIngredients}
                onChange={(e) => setPreferredIngredients(e.target.value)}
            />

            <Input
                type="text"
                placeholder="기피 성분"
                value={avoidedIngredients}
                onChange={(e) => setAvoidedIngredients(e.target.value)}
            />

            <button onClick={handleSave}>저장</button>

            {savedMessage && <p>{savedMessage} <Link to="/recommend">추천 보러 가기</Link></p>}
        </div>
    );
}

export default Profile;
