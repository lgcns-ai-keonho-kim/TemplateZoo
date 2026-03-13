# ChatSessionMemoryStore 가이드

이 문서는 `src/rag_chatbot/shared/chat/memory/session_store.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

세션별 최근 메시지를 인메모리로 유지하는 컨텍스트 저장소다.

## 2. 공개 구성

- 클래스 `ChatSessionMemoryStore`
  공개 메서드: `max_messages`, `has_session`, `ensure_session`, `replace_session`, `rpush`, `lrange`, `clear_session`

## 3. 코드 설명

- 세션 단위 최근 메시지 수 제한은 메모리 사용량과 문맥 품질을 함께 결정한다.

## 4. 유지보수/추가개발 포인트

- 메모리 저장소는 프로세스 로컬 상태이므로 멀티 인스턴스 환경에서 공유 저장소처럼 가정하면 안 된다.

## 5. 관련 문서

- `docs/shared/overview.md`
- `docs/shared/chat/README.md`
