# `nodes/message_node.py` 레퍼런스

## 1. 모듈 목적

`MessageNode`는 상태 selector를 Enum 메시지로 매핑해 사용자 출력 문구를 확정한다.

## 2. 핵심 클래스

1. `MessageNode`
- `messages`: Enum 클래스
- `selector_key`: 상태 입력 키
- `selector_to_member`: selector -> Enum member name 매핑
- `default_member`: 미매칭 시 기본 멤버

## 3. 입력/출력

1. `run(state, config=None)`
- 출력: `{output_key: selected_message}`

2. 매핑 우선순위
- `selector_to_member`
- Enum member name 직접 매칭
- Enum member value 매칭
- `default_member`

## 4. 실패 경로

1. `MESSAGE_NODE_CONFIG_INVALID`
- 조건: `messages`가 Enum 클래스 아님, `selector_key` 비어 있음

2. `MESSAGE_NODE_MAPPING_NOT_FOUND`
- 조건: selector 매핑 실패 + default 없음

3. 입력 정규화 실패
- `_state_adapter`의 `CHAT_NODE_INPUT_INVALID` 전파

## 5. 연계 모듈

1. `src/chatbot/core/chat/nodes/safeguard_message_node.py`
2. `src/chatbot/core/chat/messages/*.py`

## 6. 변경 시 영향 범위

selector 토큰 변경 시 `BranchNode`와 `MessageNode`의 매핑 테이블을 함께 맞춰야 한다.
