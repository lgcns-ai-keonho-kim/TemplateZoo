# `nodes/fanout_branch_node.py` 레퍼런스

## 1. 모듈 목적

`FanoutBranchNode`는 리스트 입력을 LangGraph `Send` 목록으로 바꿔 fan-out 분기를 수행한다.

## 2. 핵심 클래스

1. `FanoutBranchNode`
- `items_key`: fan-out 입력 리스트 키
- `target_node`: 각 항목이 전달될 노드
- `default_branch`: 입력 비정상/비어있을 때 이동할 분기

## 3. 입력/출력

1. `route(state, config=None)` / `run(state, config=None)`
- 리스트가 유효하면 `list[Send]` 반환
- 유효 항목이 없으면 `default_branch` 문자열 반환
- 리스트 원소가 `Mapping`이 아니면 무효 항목으로 집계

## 4. 실패 경로

1. `FANOUT_BRANCH_NODE_CONFIG_INVALID`
- 조건: `items_key`, `target_node`, `default_branch` 중 하나가 빈 문자열

2. 입력 정규화 실패
- `_state_adapter`의 `CHAT_NODE_INPUT_INVALID` 전파

## 5. 연계 모듈

1. `src/chatbot/core/chat/graphs/chat_graph.py`
2. `nodes/_state_adapter.py`

## 6. 변경 시 영향 범위

`items_key` 또는 `target_node` 변경 시 그래프 edge 연결과 상태 키를 동시에 수정해야 한다.
