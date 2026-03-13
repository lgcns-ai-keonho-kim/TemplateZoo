# services/service_executor.py

큐 워커와 이벤트 버퍼를 이용해 채팅 실행을 오케스트레이션하는 실행기다.

## 1. 역할

- `submit_job`으로 요청을 큐에 적재하고 worker 스레드에서 `ChatService.astream`을 소비한다.
- 그래프 이벤트를 공개 이벤트(`start`, `token`, `references`, `sql_plan`, `sql_result`, `done`, `error`)로 정규화한다.
- SSE payload를 생성해 `stream_events`로 전달한다.
- `done` 직후 assistant 메시지 저장과 assistant context 캐시 저장을 담당한다.

## 2. 핵심 상태/이벤트

| 항목 | 값 |
| --- | --- |
| 세션 상태 | `IDLE`, `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED` |
| 공개 이벤트 | `start`, `token`, `references`, `sql_plan`, `sql_result`, `done`, `error` |
| 종료 조건 | `done` 또는 `error` 전송 후 스트림 종료 |

현재 기본 그래프 기준:

- `references`는 실행기가 지원하는 공개 이벤트 타입이지만, 기본 Text-to-SQL 그래프의 `stream_node` 설정에는 포함되지 않는다.
- `done`의 `node` 값은 `response`, `blocked`, `sql_pipeline_failure_message`, `execution_failure_message` 중 하나가 될 수 있다.

## 3. 주요 메서드

| 메서드 | 설명 |
| --- | --- |
| `submit_job` | 요청 검증 및 queue put |
| `_worker_loop/_handle_job` | 큐 소비 및 단일 세션 실행 락 제어 |
| `_consume_service_astream` | 서비스 이벤트 소비/정규화 |
| `stream_events` | EventBuffer pop 후 SSE 문자열 반환 |
| `_persist_assistant_message_sync` | done 직후 assistant 저장 + 재시도 |
| `_cache_assistant_context` | 직전 assistant 컨텍스트 캐시 저장 |

## 4. 실패 경로

| 코드 | 발생 조건 |
| --- | --- |
| `CHAT_JOB_QUEUE_FAILED` | queue put 실패 |
| `CHAT_SESSION_NOT_FOUND` | 요청 세션 식별 실패 |
| `CHAT_STREAM_TIMEOUT` | 실행 시간이 timeout 초과 |

## 5. 관련 코드

- `services/chat_service.py`
- `runtime/assistant_context.py`
- `src/text_to_sql/shared/runtime/buffer/*`
- `src/text_to_sql/shared/runtime/queue/*`
