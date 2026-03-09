# memory/session_store.py

세션별 최근 메시지를 메모리에 보관하는 캐시 저장소다.

## 1. 역할

- 저장소 조회 빈도를 줄이기 위해 세션 메시지를 `deque`로 캐시한다.
- Redis 유사 인터페이스(`rpush`, `lrange`)를 제공해 상위 로직을 단순화한다.

## 2. 주요 메서드

| 메서드 | 설명 |
| --- | --- |
| `ensure_session` | 캐시가 없으면 loader로 초기 적재 |
| `replace_session` | 세션 메시지 전체 교체 |
| `rpush` | 메시지 append |
| `lrange` | 포함 범위 조회(음수 인덱스 지원) |
| `clear_session` | 세션 캐시 제거 |

## 3. 동작 규칙

- `max_messages` 초과분은 자동으로 오래된 메시지부터 제거된다.
- 외부로 반환되는 `ChatMessage`는 깊은 복사로 전달된다.
- thread-safe를 위해 `RLock`을 사용한다.

## 4. 연관 모듈

- `src/text_to_sql/shared/chat/services/chat_service.py`
- `src/text_to_sql/core/chat/models/entities.py`
