# `interface/ports.py` 레퍼런스

## 1. 모듈 목적

실행 계층 계약(Protocol)을 정의해 구현체 교체 시 호출부 변경을 줄인다.

## 2. 핵심 타입

1. `StreamNodeConfig`
- 타입: `Mapping[str, str | Sequence[str]]`
- 의미: 노드별 허용 이벤트 목록

2. `GraphPort`
- 그래프 컴파일/실행/스트리밍 계약
- 주요 메서드: `compile`, `set_stream_node`, `invoke`, `ainvoke`, `stream_events`, `astream_events`

3. `ChatServicePort`
- 세션/메시지/멱등 저장 계약
- 주요 메서드: `create_session`, `list_messages`, `persist_assistant_message`, `stream`, `astream`

4. `ServiceExecutorPort`
- 비동기 실행 오케스트레이션 계약
- 주요 메서드: `submit_job`, `stream_events`, `get_session_status`

## 3. 구현체 매핑

1. `GraphPort` -> `BaseChatGraph`
2. `ChatServicePort` -> `ChatService`
3. `ServiceExecutorPort` -> `ServiceExecutor`

## 4. 실패 경로

이 파일은 Protocol 정의만 제공하므로 직접 예외를 발생시키지 않는다.

## 5. 연계 모듈

1. `src/chatbot/shared/chat/services/chat_service.py`
2. `src/chatbot/shared/chat/services/service_executor.py`
3. `src/chatbot/shared/chat/graph/base_chat_graph.py`

## 6. 변경 시 영향 범위

1. 시그니처 변경 시 구현체와 호출부(API runtime 조립) 동시 수정 필요
2. 반환 타입 변경 시 static UI/API 응답 변환 로직 영향 확인
