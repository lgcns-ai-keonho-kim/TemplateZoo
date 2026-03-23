# Function Node

## 개요

`src/one_shot_agent/shared/agent/nodes/function_node.py` 구현을 기준으로 현재 동작을 정리한다.

주입된 함수를 실행해 state 업데이트 payload를 반환하는 범용 노드입니다.
동기/비동기 모두 지원합니다.

## 주요 구성

1. `FunctionNode.run()`: 동기 경로
2. `FunctionNode.arun()`: 비동기 경로
3. `function_node()`: 생성 헬퍼

## 검증 규칙

- 반환값은 반드시 `Mapping`이어야 합니다.
- 동기 `run()`에서 awaitable 반환은 허용되지 않습니다.

## 실패 경로

- `FUNCTION_NODE_CONFIG_INVALID`
- `FUNCTION_NODE_ASYNC_IN_SYNC_RUN`
- `FUNCTION_NODE_EXECUTION_ERROR`
- `FUNCTION_NODE_OUTPUT_INVALID`

## 관련 문서

- `docs/shared/agent/nodes/_state_adapter.md`
