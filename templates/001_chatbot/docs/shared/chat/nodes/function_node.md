# `nodes/function_node.py` 레퍼런스

## 1. 모듈 목적

`FunctionNode`는 주입 함수(`fn`)를 실행해 상태 업데이트 payload를 반환한다.

## 2. 핵심 구성

1. `FunctionNode`
- `run`: 동기 진입점
- `arun`: 비동기 진입점

2. `function_node(...)`
- 팩토리 함수
- `FunctionNode` 생성 래퍼

## 3. 입력/출력

1. 입력 함수 시그니처
- `fn(state: Mapping[str, Any]) -> Mapping[str, Any] | Awaitable[Mapping[str, Any]]`

2. 출력
- 항상 `dict[str, Any]`
- 키는 문자열로 강제 변환

## 4. 실패 경로

1. `FUNCTION_NODE_CONFIG_INVALID`
- 조건: `fn`이 callable 아님, `node_name` 비어 있음

2. `FUNCTION_NODE_ASYNC_IN_SYNC_RUN`
- 조건: `run`에서 awaitable 반환

3. `FUNCTION_NODE_EXECUTION_ERROR`
- 조건: 사용자 함수 실행 중 예외

4. `FUNCTION_NODE_OUTPUT_INVALID`
- 조건: 반환값이 `Mapping`이 아님

5. 입력 정규화 실패
- `_state_adapter`의 `CHAT_NODE_INPUT_INVALID` 전파

## 5. 연계 모듈

1. `src/chatbot/core/chat/nodes/*`
2. `nodes/_state_adapter.py`

## 6. 변경 시 영향 범위

반환 payload 형식이 바뀌면 다음 노드가 기대하는 상태 키와 충돌할 수 있다.
