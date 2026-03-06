# Shared Chat 레퍼런스

이 문서는 `src/chatbot/shared/chat` 모듈의 실행 흐름, 상태 전이, SSE 이벤트 처리 동작을 정리한다.

## 1. 핵심 구성

| 구성요소 | 역할 | 파일 |
| --- | --- | --- |
| ChatService | 세션/메시지 처리, 그래프 실행 | `services/chat_service.py` |
| ServiceExecutor | 큐 소비, 이벤트 버퍼 중계, 상태 관리 | `services/service_executor.py` |
| ChatHistoryRepository | 세션/메시지/request 커밋 저장 | `repositories/history_repository.py` |

## 2. 상태 전이

`ServiceExecutor` 기준:

```text
IDLE -> QUEUED -> RUNNING -> COMPLETED
IDLE -> QUEUED -> RUNNING -> FAILED
```

기준:

1. RUNNING을 QUEUED로 역전시키지 않는다.
2. timeout/예외는 FAILED로 기록한다.

## 3. 이벤트 타입과 종료 동작

외부 표준 이벤트:

1. `start`
2. `token`
3. `done`
4. `error`

중요:

1. 종료 이벤트는 `done` 또는 `error` 둘 다 유효하다.
2. `error`는 실패 원인 전달을 위한 정상 종료 경로다.
3. 테스트에서 `done`만 성공 조건으로 강제하면 오탐이 발생할 수 있다.

## 4. 타임아웃 설정 레퍼런스

관련 변수:

1. `CHAT_STREAM_TIMEOUT_SECONDS`
2. `CHAT_EVENT_BUFFER_POLL_TIMEOUT`
3. `CHAT_JOB_QUEUE_POLL_TIMEOUT`

운영 레퍼런스:

1. 서버 timeout과 클라이언트 read timeout을 함께 조정한다.
2. 느린 LLM 응답 시간 분포를 기준으로 안전 마진을 둔다.

## 5. 멱등 저장 동작

`persist_assistant_message` 기준:

1. `is_request_committed(request_id)`로 기저장 여부 확인
2. 미저장일 때만 assistant 메시지 저장
3. 저장 성공 후 `mark_request_committed` 기록

효과:

1. 중복 `done`/재시도에도 assistant 중복 저장을 방지한다.

## 6. 트러블슈팅

| 증상 | 원인 후보 | 조치 |
| --- | --- | --- |
| SSE가 중간에 끊김 | timeout 과소, 버퍼 poll 미스매치 | timeout/poll 값 동기화 |
| `done` 대신 `error` 종료 | 노드 예외, LLM 호출 실패 | `error_message`, `metadata.error_code` 확인 |
| assistant 중복 저장 | request 커밋 체크 누락 | `is_request_committed` 경로 점검 |
| 큐 제출 실패 | 큐 포화/백엔드 불안정 | 큐 크기/연결 상태 점검 |

## 7. 관련 문서

- `docs/api/chat.md`
- `docs/shared/runtime.md`
- `docs/setup/env.md`
- `docs/setup/troubleshooting.md`
