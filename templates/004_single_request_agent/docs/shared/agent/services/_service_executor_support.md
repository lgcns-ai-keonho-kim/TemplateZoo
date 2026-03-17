# Service Executor Support

## 개요

`src/single_request_agent/shared/agent/services/_service_executor_support.py` 구현을 기준으로 현재 동작을 정리한다.

`ServiceExecutor`의 내부 보조 동작을 분리한 믹스인입니다.
영속 후처리 큐, 이벤트 정규화, SSE payload 생성, 상태 보조 로직을 제공합니다.

## 주요 메서드

1. `_persist_loop`, `_enqueue_persist_task`, `_process_persist_task`, `_retry_persist_task`
2. `_normalize_graph_event`, `_emit_event`
3. `_build_public_payload`, `_build_error_payload`, `_build_sse`
4. `_resolve_session_id`, `_resolve_*_timeout`
5. `_set_session_status`, `_get_session_lock`, `_extract_job_payload`

## 실패 경로

- `CHAT_SESSION_NOT_FOUND`: 제출 시 세션 검증 실패
- `CHAT_STREAM_TIMEOUT`: 서비스 스트림 소비 타임아웃

## 관련 문서

- `docs/shared/agent/services/service_executor.md`
- `docs/shared/agent/services/chat_service.md`
