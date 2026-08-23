// 재사용 가능한 입력창 컴포넌트
// type, placeholder, value, onChange를 외부에서 받아서 다양한 입력창으로 활용함
function Input({ type, placeholder, value, onChange }) {
    return (
        <input
            type={type}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
        />
    );
}

export default Input;