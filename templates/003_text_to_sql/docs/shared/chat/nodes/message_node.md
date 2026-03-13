# nodes/message_node.py

selector 값을 Enum 메시지로 치환하는 노드다.

## 1. 역할

- 분기/분류 결과를 사용자 노출 문구로 매핑한다.
- Enum 기반으로 메시지 텍스트 변경 지점을 한 곳으로 고정한다.

## 2. 주요 메서드

| 메서드 | 설명 |
| --- | --- |
| `run` | LangGraph 진입점 |
| `_run` | selector 읽기 및 매핑 수행 |
| `_resolve_member` | name/value/default 우선순위로 Enum 멤버 결정 |

## 3. 매핑 우선순위

1. `selector_to_member`
2. Enum member name
3. Enum member value
4. `default_member`

## 4. 실패 경로

| 코드 | 발생 조건 |
| --- | --- |
| `MESSAGE_NODE_CONFIG_INVALID` | `messages`가 Enum 클래스 아님 / `selector_key` 비어 있음 |
| `MESSAGE_NODE_MAPPING_NOT_FOUND` | selector를 멤버로 해석하지 못함 |

## 5. 관련 코드

- `src/text_to_sql/core/chat/nodes/safeguard_node.py`
- `nodes/_state_adapter.py`
