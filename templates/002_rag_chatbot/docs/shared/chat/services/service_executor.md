# Service Executor

이 문서는 `src/rag_chatbot/shared/chat/services/service_executor.py`의 실행 오케스트레이터를 설명한다.

## 1. 목적

- 채팅 요청을 비동기 큐 작업으로 처리한다.
- 그래프 이벤트를 공개 SSE 이벤트 스키마로 정규화한다.
- done 이후 assistant 메시지 저장 후처리를 재시도 정책으로 수행한다.

## 2. 구성 요소

| 구성 | 역할 |
| --- | --- |
| `job_queue` | 요청 작업 큐 |
| `event_buffer` | 요청별 이벤트 버퍼 |
| 워커 스레드 | 큐 소비 + 서비스 스트림 실행 |
| 후처리 스레드 | done 후 assistant 저장 |
| 세션 락 | 동일 세션 직렬 처리 |

세션 상태 값: `IDLE`, `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`.

## 3. 공개 메서드

1. `submit_job`: 요청을 큐에 적재하고 `session_id/request_id/status` 반환
2. `stream_events`: 버퍼 이벤트를 SSE 문자열로 반환
3. `get_session_status`: 최근 세션 실행 상태 조회
4. `shutdown`: 워커/후처리 스레드 종료

## 4. 이벤트 정규화

내부 그래프 이벤트 -> 공개 이벤트 매핑:

1. `token` -> `token`
2. `assistant_message`(blocked 노드만) -> `token`
3. `references` -> `references`
4. `done` -> `done`
5. `error` -> `error`

공개 이벤트 타입은 `start/token/references/done/error`만 허용한다.

## 5. 실행 흐름

1. `submit_job`가 큐에 작업 저장 후 상태를 `QUEUED`로 설정
2. 워커가 작업을 가져와 상태를 `RUNNING`으로 설정
3. `ChatService.astream` 소비 결과를 이벤트 버퍼로 push
4. `done` 발생 시 상태를 `COMPLETED`로 변경하고 후처리 큐에 저장 작업 적재
5. `error` 또는 타임아웃 발생 시 상태를 `FAILED`로 변경

## 6. 후처리 저장 정책

- done content가 비어 있으면 저장을 생략한다.
- 저장 실패 시 `CHAT_PERSIST_RETRY_LIMIT`/`CHAT_PERSIST_RETRY_DELAY_SECONDS` 기준으로 재시도한다.
- 재시도 한도 초과 시 에러 로그를 남기고 중단한다.

## 7. 실패/예외 포인트

1. 작업 큐 저장 실패: `CHAT_JOB_QUEUE_FAILED`
2. 스트림 대기 초과: timeout 에러 이벤트 생성
3. 그래프 소비 시간 초과: `CHAT_STREAM_TIMEOUT`
4. 프로토콜 위반 이벤트: `error` 이벤트로 변환 후 종료

## 8. 관련 문서

- `docs/shared/chat/services/chat_service.md`
- `docs/shared/chat/interface/ports.md`
- `docs/shared/runtime.md`
- `docs/api/chat.md`
