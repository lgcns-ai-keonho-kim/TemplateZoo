# `memory/session_store.py` 레퍼런스

`ChatSessionMemoryStore`는 세션별 최근 메시지를 메모리에 보관하는 경량 캐시다. 현재 `ChatService`가 문맥 윈도우를 구성할 때 사용한다.

## 1. 코드 설명

핵심 메서드:

1. `ensure_session(session_id, loader)`
2. `replace_session(session_id, messages)`
3. `rpush(session_id, message)`
4. `lrange(session_id, start, end)`
5. `clear_session(session_id)`

동작 특징:

1. 내부 저장은 `dict[str, deque[ChatMessage]]`
2. 세션별 최대 메시지 수는 `max_messages`
3. `RLock`으로 동시 접근을 보호
4. `lrange()`는 Redis `LRANGE`처럼 종료 인덱스를 포함한다

## 2. 유지보수 포인트

1. `lrange()`의 음수 인덱스 처리 규칙을 바꾸면 `ChatService._build_context_history()` 결과가 달라진다.
2. 메시지는 깊은 복사 후 저장한다. 이 정책을 제거하면 상위 계층에서 참조 공유로 상태가 오염될 수 있다.
3. 삭제 시 `clear_session()`이 호출되지 않으면 메모리에 남은 이력이 다시 노출될 수 있다.

## 3. 추가 개발/확장 가이드

1. Redis 기반 세션 메모리를 도입하더라도 현재 인터페이스(`ensure_session`, `rpush`, `lrange`)를 맞추면 `ChatService` 변경을 최소화할 수 있다.
2. 문맥 정책을 메시지 수 대신 토큰 수 기준으로 바꾸고 싶다면, 이 저장소보다는 `ChatService`의 히스토리 선택 로직에서 먼저 경계를 나누는 편이 낫다.

## 4. 관련 코드

- `src/chatbot/shared/chat/services/chat_service.py`
- `src/chatbot/core/chat/models/entities.py`
