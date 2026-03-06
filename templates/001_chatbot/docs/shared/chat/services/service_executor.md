# `services/service_executor.py` 레퍼런스

## 1. 모듈 목적

`ServiceExecutor`는 작업 큐 소비, 이벤트 버퍼 중계, 비동기 저장 후처리를 담당한다.

## 2. 핵심 클래스

1. `ServiceExecutor`
- 외부 API: `submit_job`, `stream_events`, `get_session_status`, `shutdown`
- 내부 루프: `_worker_loop`, `_persist_loop`
- 상태값: `IDLE`, `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`

## 3. 입력/출력

1. `submit_job(session_id, user_query, context_window)`
- 큐 payload를 적재하고 `session_id`, `request_id`, `QUEUED` 반환
- `session_id`가 없으면 새 세션 생성

2. `_handle_job`
- 시작 시 `start` 이벤트 emit
- `ChatService.stream` 이벤트를 SSE 표준 이벤트로 정규화
- `done` 발생 시 토큰 수 metadata 병합
- 완료 후 비동기 persist task enqueue

3. `stream_events(session_id, request_id)`
- `EventBuffer.pop` 결과를 SSE 문자열(`event: message`)로 반환
- `done/error` 수신 시 종료
- idle timeout 초과 시 `error` 이벤트 반환

4. persist 후처리
- `_process_persist_task`에서 `persist_assistant_message` 호출
- 실패 시 `persist_retry_limit`, `persist_retry_delay_seconds` 기준 재시도

## 4. 실패 경로

1. `CHAT_JOB_QUEUE_FAILED`
- 조건: submit 시 큐 적재 실패

2. `CHAT_SESSION_NOT_FOUND`
- 조건: 지정된 세션이 없는데 session_id를 강제 지정한 경우

3. `CHAT_STREAM_TIMEOUT`
- 조건: `_raise_timeout_if_needed` 시간 초과

4. 프로토콜 오류 응답
- 조건: 이벤트 타입/필수 필드 불일치
- 결과: SSE `type=error`, `status=FAILED`

5. 런타임 예외 처리
- worker/persist 루프는 예외를 로그로 남기고 다음 작업으로 진행

## 5. 연계 모듈

1. 서비스 포트: `interface/ports.py`
2. 비즈니스 서비스: `services/chat_service.py`
3. 런타임 인프라: `src/chatbot/shared/runtime/queue`, `src/chatbot/shared/runtime/buffer`

## 6. 운영 포인트

1. 세션 상태는 terminal(`COMPLETED`/`FAILED`) 이후 회귀를 막는다.
2. `token_count`는 `done.metadata`에 병합되어 관측 지표로 활용된다.
3. timeout/poll 설정 불일치 시 빈번한 `FAILED` 종료가 발생한다.

## 7. 변경 시 영향 범위

1. 공개 이벤트 필드 변경 시 `/chat/{session_id}/events` 소비자(UI/E2E) 동시 수정 필요
2. 상태 전이 정책 변경 시 모니터링 및 장애 대응 문서도 함께 갱신 필요
