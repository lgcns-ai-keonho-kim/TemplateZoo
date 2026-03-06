# Function Node

이 문서는 `src/rag_chatbot/shared/chat/nodes/function_node.py`를 설명한다.

## 1. 목적

- 주입된 함수를 LangGraph 노드로 실행하고 반환 Mapping을 상태 업데이트 payload로 변환한다.

## 2. 핵심 입력

| 입력 | 설명 |
| --- | --- |
| `fn` | 실행할 함수(동기/비동기) |
| `node_name` | 노드 식별 이름 |

## 3. 주요 메서드

1. `run(state, config=None)`
2. `arun(state, config=None)`
3. `function_node(fn, node_name, logger=None)` 팩토리 함수

## 4. 동작 규칙

- 동기 `run`에서 awaitable 반환 시 `FUNCTION_NODE_ASYNC_IN_SYNC_RUN` 예외 발생
- 출력이 Mapping이 아니면 `FUNCTION_NODE_OUTPUT_INVALID` 예외 발생
- 함수 실행 오류는 `FUNCTION_NODE_EXECUTION_ERROR`로 래핑

## 5. 관련 문서

- `docs/shared/chat/nodes/_state_adapter.md`
- `docs/core/chat.md`
