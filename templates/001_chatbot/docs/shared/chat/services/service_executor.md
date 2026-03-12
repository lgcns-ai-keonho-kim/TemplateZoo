# `services/service_executor.py` 레퍼런스

`ServiceExecutor`는 채팅 작업을 비동기로 실행하고, 그래프 이벤트를 SSE 공개 이벤트로 변환하는 오케스트레이터다.

## 1. 코드 설명

주요 공개 메서드:

1. `submit_job()`
2. `stream_events()`
3. `get_session_status()`
4. `shutdown()`

내부 구조:

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

핵심 규칙:

1. `submit_job()`에서 `session_id`가 없으면 새 세션 생성
2. `blocked` 노드의 `assistant_message`는 `token` 이벤트로 변환
3. `done` 이벤트 수신 후 비동기 저장 태스크 enqueue
4. 저장 실패는 `persist_retry_limit`, `persist_retry_delay_seconds` 기준 재시도

주요 오류 코드:

1. `CHAT_JOB_QUEUE_FAILED`
2. `CHAT_SESSION_NOT_FOUND`
3. `CHAT_STREAM_TIMEOUT`

## 2. 유지보수 포인트

1. `stream_events()`의 공개 페이로드는 정적 UI가 그대로 소비한다. 필드명(`type`, `content`, `status`, `error_message`)을 바꾸면 프런트가 깨진다.
2. `_set_session_status()`는 완료/실패 상태 회귀를 막는다. 상태 전이 규칙을 바꾸면 늦게 도착한 `QUEUED` 이벤트 같은 경쟁 조건이 다시 생길 수 있다.
3. `blocked` 경로를 `token`으로 바꾸는 현재 정책은 UI 단순화를 위한 것이다. 이 동작을 바꾸면 UI 렌더러도 같이 수정해야 한다.

## 3. 추가 개발/확장 가이드

1. 큐/버퍼 백엔드를 Redis로 바꾸는 작업은 이 클래스가 아니라 조립 지점(`runtime.py`)에서 처리하는 것이 현재 구조와 맞다.
2. 요청 취소 기능을 추가하려면 세션 락, 상태 맵, 버퍼 정리 규칙을 함께 설계해야 한다.
3. 이벤트 타입을 늘릴 때는 허용 타입 집합, 공개 페이로드 빌더, UI 소비 로직을 동시에 수정해야 한다.

## 4. 관련 코드

- `src/chatbot/shared/chat/services/chat_service.py`
- `src/chatbot/shared/runtime/queue/*`
- `src/chatbot/shared/runtime/buffer/*`
