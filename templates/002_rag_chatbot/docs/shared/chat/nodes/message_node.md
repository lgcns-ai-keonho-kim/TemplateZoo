# Message Node

이 문서는 `src/rag_chatbot/shared/chat/nodes/message_node.py`를 설명한다.

## 1. 목적

- 상태 selector 값을 Enum 메시지로 변환해 고정 응답 문구를 선택한다.

## 2. 핵심 입력

| 입력 | 설명 |
| --- | --- |
| `messages` | 메시지 Enum 클래스 |
| `selector_key` | selector 상태 키 |
| `output_key` | 출력 키(기본 `assistant_message`) |
| `selector_to_member` | selector -> Enum 멤버명 매핑 |
| `default_member` | 미매핑 시 기본 멤버 |

## 3. 주요 메서드

- `run(state, config=None) -> dict[str, str]`

출력:

- `{output_key: selected_message}`

## 4. 매핑 우선순위

1. `selector_to_member`
2. Enum 멤버명 직접 매칭
3. Enum 값 직접 매칭
4. `default_member`

매핑 실패 시 `MESSAGE_NODE_MAPPING_NOT_FOUND` 예외를 발생시킨다.

## 5. 관련 문서

- `docs/shared/chat/nodes/_state_adapter.md`
- `docs/core/chat.md`
