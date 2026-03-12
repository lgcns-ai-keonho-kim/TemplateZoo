# `nodes/function_node.py` 레퍼런스

`FunctionNode`는 상태를 입력받아 주입된 함수를 실행하고, 그 결과 `Mapping`을 LangGraph 상태 업데이트 payload로 반환하는 범용 노드다.

## 1. 코드 설명

핵심 구성:

1. `FunctionNode`
2. `function_node()` 팩토리 함수

실행 규칙:

1. `run()`은 동기 함수만 허용한다.
2. 동기 실행에서 awaitable이 반환되면 `FUNCTION_NODE_ASYNC_IN_SYNC_RUN`
3. 반환값이 `Mapping`이 아니면 `FUNCTION_NODE_OUTPUT_INVALID`
4. 실행 중 예외는 `FUNCTION_NODE_EXECUTION_ERROR`로 래핑한다.

## 2. 유지보수 포인트

1. 이 노드는 함수 결과의 키를 문자열로 강제 변환한다. 숫자 키나 Enum 키를 반환하면 문자열화된다는 점을 염두에 둬야 한다.
2. 실행 예외는 모두 도메인 예외로 감싸기 때문에, 원본 예외 메시지가 필요하면 `detail.metadata["error"]`를 확인해야 한다.

## 3. 추가 개발/확장 가이드

1. 간단한 상태 계산 노드는 별도 클래스를 새로 만드는 대신 `FunctionNode`로 충분한 경우가 많다.
2. 재사용할 함수가 동기/비동기 혼합이면 `run`과 `arun` 호출 경계를 명확히 나누는 편이 안전하다.

## 4. 관련 코드

- `src/chatbot/shared/chat/nodes/_state_adapter.py`
- `src/chatbot/core/chat/nodes/*`
