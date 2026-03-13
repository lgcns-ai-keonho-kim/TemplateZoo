# ChatService 가이드

이 문서는 `src/rag_chatbot/shared/chat/services/chat_service.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

세션 관리, 메시지 저장, 그래프 실행, assistant 응답 영속화를 조합하는 서비스 계층이다.

## 2. 공개 구성

- 클래스 `ChatService`
  공개 메서드: `memory_store`, `close`, `create_session`, `list_sessions`, `get_session`, `list_messages`, `delete_session`, `invoke`, `ainvoke`, `stream`, `astream`, `persist_assistant_message`, `append_assistant_message`

## 3. 코드 설명

- 세션 CRUD와 그래프 실행 경로가 한 서비스에 모여 있다.
- 최근 메시지는 메모리 저장소와 영속 저장소를 함께 사용해 관리한다.
- assistant 응답 저장은 request_id 멱등 커밋과 함께 처리한다.

## 4. 유지보수/추가개발 포인트

- 응답 저장 정책을 바꾸면 `ServiceExecutor` 후처리와 request_id 멱등 규칙을 함께 확인해야 한다.
- 메모리 정책과 저장소 조회 정책이 엇갈리면 문맥 품질이 흔들릴 수 있으므로 함께 수정하는 편이 안전하다.

## 5. 관련 문서

- `docs/shared/overview.md`
- `docs/shared/chat/README.md`
