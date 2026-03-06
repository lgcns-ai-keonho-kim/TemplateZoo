# Fanout Branch Node

이 문서는 `src/rag_chatbot/shared/chat/nodes/fanout_branch_node.py`를 설명한다.

## 1. 목적

- 리스트 입력을 `Send` 목록으로 변환해 fan-out 분기 라우팅을 수행한다.

## 2. 핵심 입력

| 입력 | 설명 |
| --- | --- |
| `items_key` | fan-out 대상 목록 키 |
| `target_node` | 각 항목을 전달할 노드 |
| `default_branch` | 목록 비정상/비어있을 때 이동할 분기 |

## 3. 주요 메서드

1. `route(state, config=None) -> str | list[Send]`
2. `run(state, config=None) -> str | list[Send]`

동작:

- `items_key` 값이 `list[Mapping]`이면 `Send(target_node, item)` 목록 반환
- 유효 항목이 없으면 `default_branch` 문자열 반환

## 4. 실패/예외 포인트

- 생성자 입력(`items_key`, `target_node`, `default_branch`)이 비어 있으면 `FANOUT_BRANCH_NODE_CONFIG_INVALID` 예외

## 5. 관련 문서

- `docs/shared/chat/nodes/_state_adapter.md`
- `docs/core/chat.md`
