# GraphPort 가이드

이 문서는 `src/rag_chatbot/shared/chat/interface/ports.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

그래프, 서비스, 실행기 사이의 포트 인터페이스를 정의한다.

## 2. 공개 구성

- 클래스 `GraphPort`
  공개 메서드: `compile`, `set_stream_node`, `invoke`, `ainvoke`, `stream_events`, `astream_events`
- 클래스 `ChatServicePort`
  공개 메서드: `close`, `create_session`, `list_sessions`, `get_session`, `list_messages`, `delete_session`, `persist_assistant_message`, `invoke`, `ainvoke`, `stream`, `astream`
- 클래스 `ServiceExecutorPort`
  공개 메서드: `submit_job`, `stream_events`, `get_session_status`

## 3. 코드 설명

- 구현체를 교체할 때는 먼저 포트 시그니처와 반환 타입을 유지해야 상위 계층이 깨지지 않는다.

## 4. 유지보수/추가개발 포인트

- 포트 변경은 구현체와 상위 호출부를 동시에 깨뜨리므로 실제 두 구현 이상이 필요할 때만 확장하는 편이 안전하다.

## 5. 관련 문서

- `docs/shared/overview.md`
- `docs/shared/chat/README.md`
