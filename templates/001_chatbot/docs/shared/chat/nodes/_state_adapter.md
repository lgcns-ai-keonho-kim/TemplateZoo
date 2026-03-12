# `nodes/_state_adapter.py` 레퍼런스

이 모듈은 LangGraph 노드 입력 `state`를 `Mapping[str, Any]`로 정규화한다. 공용 노드가 다양한 입력 타입을 동일하게 처리하도록 만드는 얇은 어댑터다.

## 1. 코드 설명

지원 입력:

1. `Mapping`
2. dataclass 인스턴스
3. `model_dump()`를 가진 객체
4. 레거시 `dict()` 메서드를 가진 객체

지원하지 않는 타입이면 `CHAT_NODE_INPUT_INVALID`를 담은 `BaseAppException`을 발생시킨다.

## 2. 유지보수 포인트

1. 이 함수는 `LLMNode`, `BranchNode`, `MessageNode`, `FunctionNode`, `FanoutBranchNode`의 공통 타입 경계다.
2. 허용 타입을 넓히면 편해 보일 수 있지만, 잘못된 객체를 조용히 받아들이면 노드 디버깅이 어려워진다.

## 3. 추가 개발/확장 가이드

1. 새 공용 노드를 만들 때 입력 정규화가 필요하면 이 함수를 먼저 재사용하는 것이 좋다.
2. 지원 타입을 늘릴 때는 항상 명시적인 실패 코드와 원인 문자열을 유지해야 상위 계층 로그 추적이 쉽다.

## 4. 관련 코드

- `src/chatbot/shared/chat/nodes/llm_node.py`
- `src/chatbot/shared/chat/nodes/branch_node.py`
- `src/chatbot/shared/chat/nodes/message_node.py`
