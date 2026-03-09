# nodes/_state_adapter.py

공용 노드 입력을 `Mapping[str, Any]`로 강제 변환하는 어댑터다.

## 1. 역할

- Mapping, dataclass, Pydantic(`model_dump`), legacy `dict()` 객체를 동일한 state 형식으로 정규화한다.
- 노드 구현이 입력 타입 분기 없이 key 기반 접근만 하도록 보장한다.

## 2. 공개 함수

| 함수 | 설명 |
| --- | --- |
| `coerce_state_mapping(state)` | 노드 입력 state를 Mapping으로 변환 |

## 3. 실패 경로

| 코드 | 발생 조건 |
| --- | --- |
| `CHAT_NODE_INPUT_INVALID` | 지원하지 않는 state 타입 입력 |

## 4. 연관 모듈

- `nodes/llm_node.py`
- `nodes/branch_node.py`
- `nodes/message_node.py`
