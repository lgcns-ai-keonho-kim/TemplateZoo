# `memory/session_store.py` 레퍼런스

## 1. 모듈 목적

`ChatSessionMemoryStore`는 세션별 최근 메시지 캐시를 메모리에 유지한다.

- `rpush/lrange` 중심 인터페이스
- 세션별 최대 보관 개수(`max_messages`) 제한
- 스레드 안전성(`RLock`) 보장

## 2. 핵심 클래스

1. `ChatSessionMemoryStore`
- 생성자 인자: `max_messages`, `logger`
- 내부 저장: `dict[str, deque[ChatMessage]]`

## 3. 입력/출력

1. `ensure_session(session_id, loader)`
- 세션이 없을 때만 `loader()` 결과로 초기화
- 이미 존재하면 무시

2. `rpush(session_id, message)`
- 메시지 1건 append
- `deque(maxlen=...)`로 오래된 메시지 자동 제거

3. `lrange(session_id, start, end)`
- Redis `LRANGE`와 동일한 포함 범위 처리
- 음수 인덱스 지원

4. `replace_session`, `clear_session`, `has_session`
- 세션 전체 교체/제거/존재 확인

## 4. 실패 경로

- 외부 예외 코드를 명시적으로 던지지 않는다.
- 전달된 `ChatMessage` 복사(`model_copy`/`model_dump`) 실패 시 런타임 오류가 상위로 전파된다.

## 5. 연계 모듈

1. `src/chatbot/shared/chat/services/chat_service.py`
2. `src/chatbot/core/chat/models/entities.py`

## 6. 변경 시 영향 범위

1. `lrange` 인덱스 해석 변경 시 문맥 윈도우(`context_window`) 동작이 달라짐
2. 보관 수 정책 변경 시 `CHAT_MEMORY_MAX_MESSAGES` 환경값과 동기화 필요
