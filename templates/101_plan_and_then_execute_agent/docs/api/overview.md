# API 모듈 개요

이 문서는 `src/plan_and_then_execute_agent/api` 계층의 실행 구조와 수정 절차를 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 코드 |
| --- | --- | --- |
| 라우터 | HTTP 요청 경로와 메서드를 정의하는 진입점 | `src/plan_and_then_execute_agent/api/*/routers/*.py` |
| DTO | 요청/응답 본문을 검증/직렬화하는 모델 | `src/plan_and_then_execute_agent/api/*/models/*.py` |
| 의존성 주입 | 라우터가 구현체를 직접 생성하지 않고 주입 함수로 받는 방식 | `src/plan_and_then_execute_agent/api/chat/services/runtime.py`, `src/plan_and_then_execute_agent/api/ui/services/__init__.py` |
| 작업 큐 | 채팅 실행 요청을 비동기 처리하기 위해 적재하는 큐 | `src/plan_and_then_execute_agent/shared/chat/services/service_executor.py` |
| 이벤트 버퍼 | SSE 구독 요청이 소비할 이벤트 저장소 | `src/plan_and_then_execute_agent/shared/runtime/*` |
| 세션 스냅샷 | 특정 세션의 메시지 목록과 최근 상태를 함께 조회하는 응답 | `src/plan_and_then_execute_agent/api/chat/routers/get_chat_session.py` |
| 정적 UI 마운트 | FastAPI가 정적 파일을 `/ui` 경로로 제공하는 설정 | `src/plan_and_then_execute_agent/api/main.py` |

## 2. 디렉터리와 스크립트 맵

| 영역 | 경로 | 책임 |
| --- | --- | --- |
| 앱 엔트리 | `src/plan_and_then_execute_agent/api/main.py` | 앱 생성, 라우터 등록, `/ui` 마운트, 종료 시 리소스 정리 |
| Chat API | `src/plan_and_then_execute_agent/api/chat` | 작업 제출, SSE 이벤트 구독, 세션 스냅샷 조회 |
| UI API | `src/plan_and_then_execute_agent/api/ui` | 세션 생성, 목록 조회, 메시지 조회, 삭제 |
| Health API | `src/plan_and_then_execute_agent/api/health` | 프로세스 생존 상태 확인 |
| API 상수 | `src/plan_and_then_execute_agent/api/const` | prefix/path/tag 상수 통합 |

주요 연결 스크립트:

1. `src/plan_and_then_execute_agent/api/main.py`
2. `src/plan_and_then_execute_agent/api/chat/routers/router.py`
3. `src/plan_and_then_execute_agent/api/ui/routers/router.py`
4. `src/plan_and_then_execute_agent/api/chat/services/runtime.py`
5. `src/plan_and_then_execute_agent/shared/chat/services/service_executor.py`
6. `src/plan_and_then_execute_agent/shared/chat/services/chat_service.py`

## 3. 라우터 등록 순서와 실행 의미

`src/plan_and_then_execute_agent/api/main.py` 기준 등록 순서:

1. `health_router`
2. `chat_router`
3. `ui_chat_router`

의미:

1. 헬스체크는 외부 모니터링이 가장 먼저 접근하는 경로로 유지한다.
2. 채팅 실행 경계와 UI 조회 경계를 라우터 레벨에서 분리해 변경 영향도를 줄인다.
3. 앱 종료 시 `shutdown_chat_api_service()`를 호출해 워커 스레드와 저장소 리소스를 정리한다.

## 4. HTTP 인터페이스 목록

| 영역 | Method | Path | 상태코드 | 구현 파일 |
| --- | --- | --- | --- | --- |
| Health | `GET` | `/health` | `200` | `src/plan_and_then_execute_agent/api/health/routers/server.py` |
| Chat | `POST` | `/chat` | `202` | `src/plan_and_then_execute_agent/api/chat/routers/create_chat.py` |
| Chat | `GET` | `/chat/{session_id}/events` | `200` | `src/plan_and_then_execute_agent/api/chat/routers/stream_chat_events.py` |
| Chat | `GET` | `/chat/{session_id}` | `200` | `src/plan_and_then_execute_agent/api/chat/routers/get_chat_session.py` |
| UI Chat | `POST` | `/ui-api/chat/sessions` | `201` | `src/plan_and_then_execute_agent/api/ui/routers/create_session.py` |
| UI Chat | `GET` | `/ui-api/chat/sessions` | `200` | `src/plan_and_then_execute_agent/api/ui/routers/list_sessions.py` |
| UI Chat | `GET` | `/ui-api/chat/sessions/{session_id}/messages` | `200` | `src/plan_and_then_execute_agent/api/ui/routers/list_messages.py` |
| UI Chat | `DELETE` | `/ui-api/chat/sessions/{session_id}` | `200` | `src/plan_and_then_execute_agent/api/ui/routers/delete_session.py` |

## 5. 예외 처리 경계

공통 원칙:

1. 도메인 예외는 `BaseAppException`으로 통일한다.
2. 라우터는 `to_http_exception()`으로 상태코드를 매핑한다.
3. 세부 오류 코드는 `detail.code`로 전달한다.

매핑 파일:

1. Chat API: `src/plan_and_then_execute_agent/api/chat/routers/common.py`
2. UI API: `src/plan_and_then_execute_agent/api/ui/routers/common.py`

## 6. 확장 포인트

### 6-1. Chat 엔드포인트 추가

1. Chat 엔드포인트 확장은 `api/chat/models`의 DTO와 `api/chat/routers`의 라우터 등록 경로를 함께 변경한다.
2. 라우터 집계 파일(`api/chat/routers/router.py`)에는 신규 라우터 `include_router` 등록이 반영된다.
3. 비즈니스 로직은 기존과 동일하게 `shared/chat/services` 계층으로 위임된다.
4. 호출 흐름 문서는 `docs/api/chat.md`와 `docs/static/ui.md`가 동시에 갱신된다.

### 6-2. UI 조회 동작 변경

1. UI 조회 동작 변경은 `api/ui/services/chat_service.py`의 조회/변환 경로에서 발생한다.
2. 해당 변경은 `api/ui/models`와 `api/ui/utils/mappers.py`의 매핑 구조에 직접 반영된다.
3. 응답 예시와 페이지 기본값 설명은 `docs/api/ui.md`에서 같은 기준으로 유지된다.

### 6-3. 런타임 조립 변경

1. 큐/버퍼/타임아웃 조립 변경 지점은 `api/chat/services/runtime.py`다.
2. 라우터 계층은 런타임 구현체 직접 생성 없이 주입 경계를 유지한다.
3. 종료 정리는 `api/main.py`의 lifespan 경계에서 동일하게 수행된다.

## 8. 관련 문서

- `docs/api/chat.md`
- `docs/api/ui.md`
- `docs/api/health.md`
- `docs/core/overview.md`
- `docs/shared/runtime.md`
