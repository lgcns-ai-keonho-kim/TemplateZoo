# Service Executor

## 개요

`src/tool_proxy_agent/shared/chat/services/service_executor.py` 구현을 기준으로 현재 동작을 정리한다.

작업 큐 소비와 SSE 이벤트 중계를 담당하는 실행 오케스트레이터입니다.
세션별 직렬 실행, 상태 전이, 완료 후 영속 후처리를 관리합니다.

## 주요 메서드

1. `submit_job()`: 요청 큐 적재 및 `QUEUED` 반환
2. `stream_events()`: 요청 단위 SSE 스트림 생성
3. `get_session_status()`: 최근 세션 상태 조회
4. `shutdown()`: worker/persist thread 종료

## 내부 상태

- `IDLE`, `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`
- 같은 `session_id`는 세션 락으로 직렬 처리됩니다.

## 이벤트 계약

- 허용 타입: `start`, `token`, `references`, `tool_start`, `tool_result`, `tool_error`, `done`, `error`
- 스트림 종료 조건: `done` 또는 `error`

## 실패 경로

- `CHAT_JOB_QUEUE_FAILED`: 큐 put 실패
- timeout 시 `type=error`, `status=FAILED` payload 반환
- 필수 Tool 실패가 retry 한도 뒤에도 남으면 `type=error`, `status=FAILED`로 종료됩니다.
- optional Tool 실패만 남은 경우에는 `done`, `status=COMPLETED`로 종료되고 부분 성공 사실은 응답 문구에 반영됩니다.

## 관련 문서

- `docs/shared/chat/services/_service_executor_support.md`
- `docs/shared/chat/services/chat_service.md`
- `docs/shared/chat/interface/ports.md`
