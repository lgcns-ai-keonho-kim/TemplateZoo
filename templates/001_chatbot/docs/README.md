# 개발 문서 허브

이 문서는 `src/chatbot` 기준으로 문서를 빠르게 찾고, 현재 코드 구조에 맞춰 기능을 유지보수하거나 확장할 때 참고할 진입점이다.

## 1. 시스템 개요

현재 애플리케이션은 다음 흐름으로 동작한다.

1. 브라우저 UI가 `/ui-api/chat/*`로 세션과 메시지를 조회한다.
2. 사용자가 메시지를 전송하면 `/chat`이 작업을 큐에 적재한다.
3. `ServiceExecutor`가 큐를 소비하며 `ChatService`를 통해 그래프를 실행한다.
4. `chat_graph`가 `safeguard -> safeguard_route -> response/blocked` 순서로 동작한다.
5. 스트림 이벤트는 SSE로 중계되고, 완료 응답은 `request_id` 기준으로 1회만 저장된다.

핵심 코드 경로:

- 앱 엔트리: `src/chatbot/api/main.py`
- 런타임 조립: `src/chatbot/api/chat/services/runtime.py`
- 도메인 그래프: `src/chatbot/core/chat/graphs/chat_graph.py`
- 실행 오케스트레이션: `src/chatbot/shared/chat/services/service_executor.py`
- 이력 저장소: `src/chatbot/shared/chat/repositories/history_repository.py`
- 정적 UI: `src/chatbot/static/*`

## 2. 문서 구조

```text
docs/
  README.md
  api/
  core/
  shared/
  integrations/
  setup/
  static/
```

| 영역 | 다루는 내용 | 먼저 읽을 문서 |
| --- | --- | --- |
| `docs/api` | HTTP 엔드포인트, DTO, 예외 매핑, 런타임 조립 | `docs/api/overview.md` |
| `docs/core` | 채팅 도메인 모델, 프롬프트, 노드, 그래프 | `docs/core/overview.md` |
| `docs/shared` | 실행 서비스, 저장소, 메모리, 설정, 로깅, 예외 | `docs/shared/overview.md` |
| `docs/integrations` | DB/LLM/FS 어댑터와 외부 시스템 연동 | `docs/integrations/overview.md` |
| `docs/setup` | 환경 변수, 로컬 실행, 인프라 준비, 장애 대응 | `docs/setup/overview.md` |
| `docs/static` | 브라우저 UI와 API 연결 방식 | `docs/static/ui.md` |

## 3. 코드와 문서의 대응 관계

| 코드 경로 | 문서 |
| --- | --- |
| `src/chatbot/api` | `docs/api/overview.md` |
| `src/chatbot/core/chat` | `docs/core/chat.md` |
| `src/chatbot/shared/chat` | `docs/shared/chat/overview.md` |
| `src/chatbot/shared/config` | `docs/shared/config.md` |
| `src/chatbot/shared/runtime` | `docs/shared/runtime.md` |
| `src/chatbot/shared/logging` | `docs/shared/logging.md` |
| `src/chatbot/shared/exceptions` | `docs/shared/exceptions.md` |
| `src/chatbot/integrations/db` | `docs/integrations/db/overview.md` |
| `src/chatbot/integrations/llm` | `docs/integrations/llm/overview.md` |
| `src/chatbot/integrations/fs` | `docs/integrations/fs/overview.md` |
| `src/chatbot/static` | `docs/static/ui.md` |

## 4. 권장 읽기 순서

### 4-1. 처음 구조를 파악할 때

1. `docs/api/overview.md`
2. `docs/core/overview.md`
3. `docs/shared/overview.md`
4. `docs/integrations/overview.md`
5. `docs/static/ui.md`

### 4-2. 채팅 실행 흐름을 수정할 때

1. `docs/api/chat.md`
2. `docs/core/chat.md`
3. `docs/shared/chat/services/chat_service.md`
4. `docs/shared/chat/services/service_executor.md`
5. `docs/static/ui.md`

### 4-3. 저장소나 인프라를 바꿀 때

1. `docs/shared/chat/repositories/history_repository.md`
2. `docs/integrations/db/overview.md`
3. `docs/setup/env.md`
4. `docs/setup/troubleshooting.md`

## 5. 유지보수 포인트

1. `request_id`는 SSE 구독과 완료 저장 멱등성을 동시에 연결하는 식별자이므로, 이름이나 의미를 바꾸면 `api`, `shared`, `static` 문서를 함께 갱신해야 한다.
2. 노드 출력 키는 `assistant_message`, `safeguard_result`, `safeguard_route`를 기준으로 연결되므로, 상태 키를 변경할 때는 `core`와 `shared` 문서를 함께 확인해야 한다.
3. 환경 변수는 import 시점에 고정 반영되는 모듈이 있으므로, `.env`와 `src/chatbot/resources/<env>/.env` 변경 후 재시작 기준을 문서와 함께 유지해야 한다.
4. 저장소 기본 경로는 SQLite이고, 다른 엔진은 선택 주입 방식이므로 `기본 동작`과 `확장 경로`를 혼동하지 않도록 문서에서 분리해야 한다.

## 6. 추가 개발과 확장 진입점

### 6-1. 새 API 추가

1. `src/chatbot/api/*/models`에 DTO를 정의한다.
2. `src/chatbot/api/*/routers`에 라우터를 추가한다.
3. 비즈니스 로직은 `src/chatbot/shared/chat/services` 또는 관련 서비스 계층으로 위임한다.
4. 문서는 `docs/api/*`와 필요한 경우 `docs/static/ui.md`까지 같이 갱신한다.

### 6-2. 그래프 분기 추가

1. `src/chatbot/core/chat/prompts`와 `src/chatbot/core/chat/nodes`를 먼저 변경한다.
2. `src/chatbot/core/chat/graphs/chat_graph.py`의 노드와 엣지를 갱신한다.
3. `stream_node` 정책과 SSE 반영 방식을 함께 확인한다.
4. 관련 문서는 `docs/core/chat.md`, `docs/shared/chat/services/service_executor.md`, `docs/api/chat.md`를 함께 수정한다.

### 6-3. 저장 엔진 교체

1. 엔진 구현은 `src/chatbot/integrations/db/engines/*`에 둔다.
2. 저장소 교체는 `src/chatbot/api/chat/services/runtime.py` 조립 단계에서 수행한다.
3. `ChatHistoryRepository`가 기대하는 CRUD/정렬/필터 계약을 먼저 만족시켜야 한다.
4. 문서는 `docs/integrations/db/*`, `docs/setup/*`, `docs/shared/chat/repositories/history_repository.md`를 함께 갱신한다.

## 7. 문서 점검 기준

1. 경로, 클래스명, 함수명이 실제 코드와 일치해야 한다.
2. 엔드포인트 경로와 응답 필드명이 실제 FastAPI 모델과 일치해야 한다.
3. 기본값은 `.env.sample`이나 코드 상수 중 실제 런타임에 사용되는 값을 기준으로 적어야 한다.
4. 기본 구현과 확장 구현을 구분해 적어야 한다.
5. 유지보수 포인트와 확장 포인트는 코드 경계 기준으로 설명해야 한다.

## 8. 주요 문서

- `docs/api/overview.md`
- `docs/core/chat.md`
- `docs/shared/chat/services/service_executor.md`
- `docs/shared/chat/repositories/history_repository.md`
- `docs/integrations/db/overview.md`
- `docs/integrations/llm/client.md`
- `docs/setup/env.md`
- `docs/setup/troubleshooting.md`
- `docs/static/ui.md`
