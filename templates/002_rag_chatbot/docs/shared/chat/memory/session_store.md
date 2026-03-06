# Chat Session Memory Store

이 문서는 `src/rag_chatbot/shared/chat/memory/session_store.py`의 세션 메모리 저장소를 설명한다.

## 1. 목적

- 세션별 최근 메시지를 메모리(deque)로 캐시한다.
- Redis `RPUSH/LRANGE`와 유사한 인터페이스를 제공한다.

## 2. 상태 모델

| 필드 | 설명 |
| --- | --- |
| `_sessions` | `session_id -> deque[ChatMessage]` |
| `_max_messages` | 세션별 최대 메시지 보관 수 (최소 1) |
| `_lock` | 동시 접근 보호용 `RLock` |

## 3. 주요 메서드

1. `has_session(session_id)`: 세션 캐시 존재 여부 조회
2. `ensure_session(session_id, loader)`: 없으면 저장소 로더로 초기화
3. `replace_session(session_id, messages)`: 세션 메시지 전체 교체
4. `rpush(session_id, message)`: 우측 삽입
5. `lrange(session_id, start, end)`: 포함 범위 조회
6. `clear_session(session_id)`: 세션 캐시 제거

## 4. 동작 포인트

- 모든 입력 메시지는 deep copy 후 저장한다.
- `deque(maxlen=max_messages)`로 초과분을 자동 제거한다.
- `lrange`는 음수 인덱스를 포함해 Redis 스타일로 해석한다.

## 5. 실패/주의 포인트

- 잘못된 인덱스 범위는 빈 리스트를 반환한다.
- 세션 캐시 초기화 전후 동시 접근은 이중 체크로 보호한다.

## 6. 관련 문서

- `docs/shared/chat/services/chat_service.md`
- `docs/shared/chat/repositories/history_repository.md`
