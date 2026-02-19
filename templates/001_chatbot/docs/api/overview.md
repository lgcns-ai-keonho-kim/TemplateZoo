# API 모듈 가이드

이 문서는 `src/chatbot/api` 계층의 실행 구조와 수정 절차를 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 코드 |
| --- | --- | --- |
| 라우터 | HTTP 요청 경로와 메서드를 정의하는 진입점 | `src/chatbot/api/*/routers/*.py` |
| DTO | 요청/응답 본문을 검증/직렬화하는 모델 | `src/chatbot/api/*/models/*.py` |
| 의존성 주입 | 라우터가 구현체를 직접 생성하지 않고 주입 함수로 받는 방식 | `src/chatbot/api/chat/services/runtime.py`, `src/chatbot/api/ui/services/__init__.py` |
| 작업 큐 | 채팅 실행 요청을 비동기 처리하기 위해 적재하는 큐 | `src/chatbot/shared/chat/services/service_executor.py` |
| 이벤트 버퍼 | SSE 구독 요청이 소비할 이벤트 저장소 | `src/chatbot/shared/runtime/*` |
| 세션 스냅샷 | 특정 세션의 메시지 목록과 최근 상태를 함께 조회하는 응답 | `src/chatbot/api/chat/routers/get_chat_session.py` |
| 정적 UI 마운트 | FastAPI가 정적 파일을 `/ui` 경로로 제공하는 설정 | `src/chatbot/api/main.py` |

## 2. 디렉터리와 스크립트 맵

| 영역 | 경로 | 책임 |
| --- | --- | --- |
| 앱 엔트리 | `src/chatbot/api/main.py` | 앱 생성, 라우터 등록, `/ui` 마운트, 종료 시 리소스 정리 |
| Chat API | `src/chatbot/api/chat` | 작업 제출, SSE 이벤트 구독, 세션 스냅샷 조회 |
| UI API | `src/chatbot/api/ui` | 세션 생성, 목록 조회, 메시지 조회, 삭제 |
| Health API | `src/chatbot/api/health` | 프로세스 생존 상태 확인 |
| API 상수 | `src/chatbot/api/const` | prefix/path/tag 상수 통합 |

주요 연결 스크립트:

1. `src/chatbot/api/main.py`
2. `src/chatbot/api/chat/routers/router.py`
3. `src/chatbot/api/ui/routers/router.py`
4. `src/chatbot/api/chat/services/runtime.py`
5. `src/chatbot/shared/chat/services/service_executor.py`
6. `src/chatbot/shared/chat/services/chat_service.py`

## 3. 라우터 등록 순서와 실행 의미

`src/chatbot/api/main.py` 기준 등록 순서:

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
| Health | `GET` | `/health` | `200` | `src/chatbot/api/health/routers/server.py` |
| Chat | `POST` | `/chat` | `202` | `src/chatbot/api/chat/routers/create_chat.py` |
| Chat | `GET` | `/chat/{session_id}/events` | `200` | `src/chatbot/api/chat/routers/stream_chat_events.py` |
| Chat | `GET` | `/chat/{session_id}` | `200` | `src/chatbot/api/chat/routers/get_chat_session.py` |
| UI Chat | `POST` | `/ui-api/chat/sessions` | `201` | `src/chatbot/api/ui/routers/create_session.py` |
| UI Chat | `GET` | `/ui-api/chat/sessions` | `200` | `src/chatbot/api/ui/routers/list_sessions.py` |
| UI Chat | `GET` | `/ui-api/chat/sessions/{session_id}/messages` | `200` | `src/chatbot/api/ui/routers/list_messages.py` |
| UI Chat | `DELETE` | `/ui-api/chat/sessions/{session_id}` | `200` | `src/chatbot/api/ui/routers/delete_session.py` |

## 5. 예외 처리 경계

공통 원칙:

1. 도메인 예외는 `BaseAppException`으로 통일한다.
2. 라우터는 `to_http_exception()`으로 상태코드를 매핑한다.
3. 세부 오류 코드는 `detail.code`로 전달한다.

매핑 파일:

1. Chat API: `src/chatbot/api/chat/routers/common.py`
2. UI API: `src/chatbot/api/ui/routers/common.py`

## 6. 변경 작업 절차

### 6-1. Chat 엔드포인트 추가

1. `src/chatbot/api/chat/models`에 DTO를 추가한다.
2. `src/chatbot/api/chat/routers`에 라우터 파일을 추가한다.
3. `src/chatbot/api/chat/routers/router.py`에 `include_router`를 등록한다.
4. 비즈니스 로직은 `src/chatbot/shared/chat/services`로 위임한다.
5. `docs/api/chat.md`와 `docs/static/ui.md`의 호출 순서를 함께 갱신한다.

### 6-2. UI 조회 정책 변경

1. `src/chatbot/api/ui/services/chat_service.py`에서 조회/변환 정책을 수정한다.
2. `src/chatbot/api/ui/models`와 `src/chatbot/api/ui/utils/mappers.py`를 동기화한다.
3. `docs/api/ui.md`의 응답 예시와 기본 페이지 규칙을 갱신한다.

### 6-3. 런타임 조립 변경

1. 큐/버퍼/타임아웃 정책은 `src/chatbot/api/chat/services/runtime.py`에서 변경한다.
2. 라우터에서 런타임 구현체를 직접 생성하지 않는다.
3. 종료 훅은 `src/chatbot/api/main.py`의 lifespan 경계를 유지한다.

## 7. 소스 매칭 점검 항목

1. 문서의 엔드포인트 경로가 `src/chatbot/api/const/chat.py` 상수 조합과 일치하는가
2. 문서의 상태코드가 라우터 데코레이터 설정과 일치하는가
3. 예외 매핑 표가 `common.py`의 실제 코드와 일치하는가
4. 페이지네이션 기본값 설명이 `src/chatbot/core/chat/const/settings.py`와 일치하는가
5. 문서에 기재한 파일 경로가 실제 저장소에 존재하는가

## 8. 관련 문서

- `docs/api/chat.md`
- `docs/api/ui.md`
- `docs/api/health.md`
- `docs/core/overview.md`
- `docs/shared/runtime.md`
