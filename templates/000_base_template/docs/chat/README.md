# Chat 아키텍처 명세

이 문서는 현재 Chat 시스템의 계층 구조, 실행 흐름, 저장 전략, 의존성 경계를 정의한다.

## 계층 책임 선언

1. `src/base_template/api/*/routers`는 HTTP 경계(요청/응답, 상태코드, 예외 매핑)만 담당한다.
2. `src/base_template/api/chat/services`, `src/base_template/api/ui/services`는 물리적으로 `api/` 하위에 위치하지만 논리적으로 Application Service 계층이며, 유스케이스 오케스트레이션만 담당한다.
3. `src/base_template/core`는 애플리케이션 핵심 구현 계층이며 HTTP 프레임워크 타입에 의존하지 않는다.

## 모듈 책임

| 모듈 | 파일 | 책임 |
| --- | --- | --- |
| API Router | `src/base_template/api/chat/routers/chat.py` | HTTP 엔드포인트 정의, 예외를 HTTP 상태코드로 변환 |
| UI Router | `src/base_template/api/ui/routers/chat.py` | UI 초기 렌더링/삭제 API 제공(세션 목록, 메시지 이력, 세션 삭제) |
| API Service (Application) | `src/base_template/api/chat/services/chat_service.py` | 라우터 요청 조립, 유스케이스 오케스트레이션, SSE 이벤트 포맷 생성 |
| UI Service (Application) | `src/base_template/api/ui/services/chat_service.py` | UI 조회/삭제 유스케이스 조립, UI 응답 모델 변환 |
| Chat Runtime | `src/base_template/api/chat/services/chat_runtime.py` | 세션/메시지 처리 오케스트레이션 |
| Task Manager | `src/base_template/api/chat/services/task_manager.py` | 큐 등록, 비동기 처리, 상태/결과/스트림 버퍼 관리 |
| Repository | `src/base_template/core/repositories/chat/history_repository.py` | 세션/메시지 영속화, 조회 |
| Graph | `src/base_template/core/chat/graphs/chat_graph.py` | LangGraph 실행, invoke/stream 호출 |
| Reply Node | `src/base_template/core/chat/nodes/reply_node.py` | LLM 메시지 구성, 모델 호출 |
| Memory Store | `src/base_template/core/common/memory/session_list_store.py` | 세션별 최근 메시지 캐시 (`rpush`, `lrange`) |

## API 계약

| 메서드 | 경로 | 입력 | 출력 |
| --- | --- | --- | --- |
| `GET` | `/ui-api/chat/sessions` | `limit`, `offset` | UI 세션 목록 |
| `GET` | `/ui-api/chat/sessions/{session_id}/messages` | `limit`, `offset` | UI 메시지 목록 |
| `DELETE` | `/ui-api/chat/sessions/{session_id}` | 경로 파라미터 | 삭제된 세션 ID |
| `POST` | `/chat/sessions` | `title`(옵션) | `session_id` |
| `GET` | `/chat/sessions` | `limit`, `offset` | 세션 목록 |
| `GET` | `/chat/sessions/{session_id}/messages` | `limit`, `offset` | 메시지 목록 |
| `POST` | `/chat/sessions/{session_id}/queue` | `message`, `context_window` | `task_id`, `queued_at` |
| `GET` | `/chat/sessions/{session_id}/tasks/{task_id}/status` | 경로 파라미터 | 태스크 상태 |
| `GET` | `/chat/sessions/{session_id}/tasks/{task_id}/result` | 경로 파라미터 | 태스크 결과 |
| `GET` | `/chat/sessions/{session_id}/tasks/{task_id}/stream` | 경로 파라미터 | SSE 스트림 |

## 실행 시퀀스

### 1. 세션 생성

1. Router가 `create_session` 요청을 수신한다.
2. API Service가 Chat Runtime `create_session`을 호출한다.
3. Runtime이 Repository를 통해 세션을 생성한다.
4. Runtime이 세션 메모리를 초기화한다.

### 2. 메시지 큐 등록

1. Router가 `queue` 요청을 수신한다.
2. API Service가 Task Manager `enqueue`를 호출한다.
3. Task Manager가 Runtime `append_user_message`를 호출한다.
4. 사용자 메시지가 DB와 메모리에 동시에 기록된다.
5. Task Manager가 `session_id + task_id` 상태를 생성하고 In-Memory Queue에 적재한다.

### 3. 비동기 처리

1. Worker가 Queue 아이템을 소비한다.
2. ThreadPool에서 태스크를 실행한다.
3. 동일 세션은 세션 락으로 순차 처리된다.
4. Runtime `process_enqueued_turn`이 문맥을 구성하고 Graph를 실행한다.
5. Graph는 Reply Node를 통해 LLM `stream` 또는 `invoke`를 실행한다.
6. 토큰 청크는 스트림 버퍼에 `rpush`된다.
7. 최종 어시스턴트 메시지가 DB와 메모리에 기록된다.

### 4. 스트리밍/조회

1. SSE 엔드포인트는 스트림 버퍼를 `lpop` 형태로 소비한다.
2. 이벤트는 `start -> token* -> done` 순서로 반환한다.
3. 실패 시 `error` 이벤트가 추가된다.
4. 상태/결과 조회는 Task Manager 상태 저장소를 기준으로 응답한다.

### 5. 세션 삭제

1. UI Router가 `DELETE /ui-api/chat/sessions/{session_id}` 요청을 수신한다.
2. UI Service가 API Service `delete_session`을 호출한다.
3. API Service가 Runtime `delete_session`을 호출한다.
4. Runtime은 Repository에서 세션과 메시지 이력을 삭제한다.
5. Runtime은 Session Memory Store에서 해당 세션 캐시를 제거한다.

## 상태 모델

태스크 상태 전이:

```text
QUEUED -> RUNNING -> STREAMING -> COMPLETED
QUEUED -> RUNNING -> FAILED
```

상태 저장 필드:

- `session_id`, `task_id`
- `created_at`, `started_at`, `completed_at`
- `status`, `error_message`
- `assistant_message`

## 저장 전략

| 저장소 | 목적 | 쓰기 시점 | 읽기 시점 |
| --- | --- | --- | --- |
| SQLite (`CHAT_DB_PATH`) | 정합성 기준 데이터 | 사용자 메시지 등록 시, 어시스턴트 응답 완료 시 | 세션/메시지 조회, 메모리 초기화 |
| Session Memory Store | 최근 문맥 캐시 | 사용자/어시스턴트 메시지 기록 시 | LLM 호출 직전 문맥 구성 |
| Task Stream Buffer | 토큰 스트림 전달 | LLM 청크 생성 시 | SSE 요청 처리 시 |

## 구조적 의존성

```text
api/ui/routers -> api/ui/services/chat_service
api/ui/services/chat_service -> api/chat/services/chat_service
api/chat/routers -> api/chat/services/chat_service
api/chat/services/chat_service -> api/chat/services/chat_runtime
api/chat/services/chat_service -> api/chat/services/task_manager
api/chat/services/task_manager -> shared/runtime (퍼사드)
api/chat/services/chat_runtime -> core/repositories/chat/history_repository
api/chat/services/chat_runtime -> core/chat/graphs/chat_graph
core/chat/graphs/chat_graph -> core/chat/nodes/reply_node
core/chat/nodes/reply_node -> integrations/llm/client
core/repositories/chat/history_repository -> integrations/db/client
```

## 동시성 규칙

1. 큐 소비는 단일 Worker 스레드 루프에서 시작한다.
2. 실제 태스크 실행은 ThreadPool에 위임한다.
3. 동일 `session_id`는 `threading.Lock`으로 직렬화한다.
4. SQLite 스레드 제약 회피를 위해 태스크 실행 시 별도 Runtime 인스턴스를 생성한다.
5. In-Memory 태스크 저장소를 사용하므로 멀티 프로세스 확장은 외부 상태 저장소(예: Redis) 전환 후 적용한다.

## 오류 전달 규칙

- 도메인/인프라 오류는 `BaseAppException`으로 통일한다.
- Router는 `detail.code` 기준으로 HTTP 상태코드를 매핑한다.
- 공통 에러 코드 예시: `CHAT_SESSION_NOT_FOUND`, `CHAT_TASK_NOT_FOUND`, `CHAT_QUEUE_ERROR`, `CHAT_QUEUE_FULL`, `CHAT_MESSAGE_EMPTY`.
