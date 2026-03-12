# `nodes/fanout_branch_node.py` 레퍼런스

`FanoutBranchNode`는 상태 안의 리스트를 `Send` 목록으로 바꿔 LangGraph fan-out 분기를 수행하는 범용 노드다. 현재 기본 채팅 그래프에서는 직접 쓰지 않지만, shared 계층의 확장용 유틸로 유지되고 있다.

## 1. 코드 설명

핵심 인자:

1. `items_key`
2. `target_node`
3. `default_branch`

동작 방식:

1. `items_key` 값이 리스트가 아니면 `default_branch`
2. 리스트 항목 중 `Mapping`만 `Send(target_node, dict(item))`으로 변환
3. 유효한 항목이 하나도 없으면 `default_branch`

실패 조건:

1. `items_key`, `target_node`, `default_branch`가 비어 있으면 `FANOUT_BRANCH_NODE_CONFIG_INVALID`

## 2. 유지보수 포인트

1. 입력 검증은 보수적으로 동작한다. 리스트 안에 잘못된 항목이 섞여 있으면 무시하고 계속 진행한다.
2. 현재 기본 채팅 경로에서 직접 사용하지 않으므로, 이 노드 변경 시 실제 사용 지점이 있는지 먼저 확인하는 편이 안전하다.

## 3. 추가 개발/확장 가이드

1. RAG나 병렬 평가 노드를 추가할 때 fan-out이 필요하면 이 노드를 재사용할 수 있다.
2. 항목별 공통 메타데이터를 주입해야 한다면 `dict(item)` 생성 단계에서만 최소 수정하는 편이 좋다.

## 4. 관련 코드

- `src/chatbot/shared/chat/nodes/_state_adapter.py`
- `src/chatbot/core/chat/graphs/chat_graph.py`
