# State Adapter

이 문서는 `src/rag_chatbot/shared/chat/nodes/_state_adapter.py`를 설명한다.

## 1. 목적

- LangGraph 노드 입력 state를 `Mapping[str, Any]` 형태로 정규화한다.
- 노드 구현에서 타입 분기 코드를 반복하지 않도록 공통 경계를 제공한다.

## 2. 지원 입력 타입

1. `Mapping`
2. dataclass 인스턴스
3. Pydantic 모델(`model_dump`)
4. 레거시 dict 변환 객체(`dict` 메서드)

## 3. 주요 함수

- `coerce_state_mapping(state) -> Mapping[str, Any]`

동작:

1. 지원 타입이면 키를 문자열로 변환해 반환
2. 지원하지 않는 타입이면 `CHAT_NODE_INPUT_INVALID` 예외 발생

## 4. 관련 문서

- `docs/shared/chat/nodes/llm_node.md`
- `docs/shared/chat/nodes/branch_node.md`
- `docs/shared/chat/nodes/message_node.md`
