# Session Store

## 개요

`src/plan_and_then_execute_agent/shared/chat/memory/session_store.py` 구현을 기준으로 현재 동작을 정리한다.

세션별 메시지 메모리 캐시를 관리합니다.
`rpush/lrange` 중심 API로 최근 메시지를 유지하며, 저장소 조회를 줄여 문맥 빌드 비용을 낮춥니다.

## 주요 메서드

1. `ensure_session()`: 세션 미존재 시 loader로 초기화
2. `replace_session()`: 세션 메시지 전체 교체
3. `rpush()`: 우측 append
4. `lrange()`: Redis와 유사한 포함 범위 조회
5. `clear_session()`: 세션 캐시 제거

## 동작 특성

- 세션별 `max_messages` 제한을 강제합니다.
- 내부 복사(`_copy_message`)로 외부 변경 전파를 차단합니다.
- `threading.RLock`으로 동시 접근을 보호합니다.

## 관련 문서

- `docs/shared/chat/services/chat_service.md`
- `docs/shared/chat/repositories/history_repository.md`
