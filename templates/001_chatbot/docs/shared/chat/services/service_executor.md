# `services/service_executor.py` 레퍼런스

`ServiceExecutor`는 채팅 작업을 비동기로 실행하고, 그래프 이벤트를 SSE 공개 이벤트로 변환하는 오케스트레이터다.

## 1. 주요 공개 메서드

1. `submit_job()`
2. `stream_events()`
3. `get_session_status()`
4. `shutdown()`

## 2. 내부 구조

1. 작업 처리용 워커 스레드
2. assistant 저장용 후처리 스레드
3. 세션별 상태 맵
4. 세션별 락

공개 이벤트 타입:

1. `start`
2. `token`
3. `done`
4. `error`

세션 상태:

1. `IDLE`
2. `QUEUED`
3. `RUNNING`
4. `COMPLETED`
5. `FAILED`

## 3. 현재 구현 특징

1. `submit_job()`에서 `session_id`가 없으면 새 세션을 만든다.
2. 워커는 `ChatService.stream()` 결과를 공개 이벤트로 정규화한다.
3. `blocked` 노드의 `assistant_message`는 공개 `token` 이벤트로 변환한다.
4. `done` 이벤트 이후에는 별도 후처리 스레드가 assistant 메시지 저장을 담당한다.
5. 저장 실패는 `persist_retry_limit`, `persist_retry_delay_seconds` 기준으로 재시도한다.

## 4. 주요 오류 코드

1. `CHAT_JOB_QUEUE_FAILED`
2. `CHAT_SESSION_NOT_FOUND`
3. `CHAT_STREAM_TIMEOUT`

## 5. 유지보수 포인트

1. 공개 SSE 페이로드 필드(`type`, `node`, `content`, `status`, `error_message`, `metadata`)는 프런트 계약이다.
2. `_set_session_status()`는 완료/실패 상태 회귀를 막는다.
3. `stream_events()`는 종료 시 `event_buffer.cleanup()`을 호출한다.
4. timeout은 예외가 아니라 공개 `error` 이벤트로도 노출될 수 있다.

## 6. 관련 문서

- `docs/api/chat.md`
- `docs/shared/runtime.md`
- `docs/static/ui.md`
