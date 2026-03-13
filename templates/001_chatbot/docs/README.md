# 개발 문서 허브

이 문서는 현재 코드 기준으로 `docs/`를 어디서 읽기 시작해야 하는지 정리한 진입점이다.

## 1. 시스템 개요

현재 애플리케이션은 아래 순서로 동작한다.

1. 정적 UI가 `/ui-api/chat/*`로 세션과 메시지를 조회한다.
2. 사용자가 메시지를 보내면 `POST /chat`이 작업을 큐에 적재한다.
3. `ServiceExecutor`가 큐를 소비하며 `ChatService`를 실행한다.
4. `chat_graph`가 `safeguard -> safeguard_route -> response/blocked` 흐름으로 처리한다.
5. 이벤트는 SSE로 중계되고, 최종 assistant 응답은 `request_id` 기준으로 1회만 저장된다.

핵심 코드 경로:

- 앱 엔트리: `src/chatbot/api/main.py`
- 런타임 조립: `src/chatbot/api/chat/services/runtime.py`
- 도메인 그래프: `src/chatbot/core/chat/graphs/chat_graph.py`
- 실행 서비스: `src/chatbot/shared/chat/services/chat_service.py`
- 실행 오케스트레이터: `src/chatbot/shared/chat/services/service_executor.py`
- 이력 저장소: `src/chatbot/shared/chat/repositories/history_repository.py`
- 정적 UI: `src/chatbot/static/`

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
| `docs/api` | HTTP 엔드포인트, DTO, 예외 매핑, 런타임 주입 | `docs/api/overview.md` |
| `docs/core` | 채팅 상태, 프롬프트, 노드, 그래프 | `docs/core/overview.md` |
| `docs/shared` | 실행 서비스, 저장소, 메모리, 런타임 유틸, 로깅, 예외 | `docs/shared/overview.md` |
| `docs/integrations` | DB, LLM, 파일 시스템 연동 | `docs/integrations/overview.md` |
| `docs/setup` | 환경 변수, 로컬 실행, 장애 대응 | `docs/setup/overview.md` |
| `docs/static` | 브라우저 UI와 백엔드 계약 | `docs/static/ui.md` |

## 3. 권장 읽기 순서

### 3-1. 처음 구조를 파악할 때

1. `docs/api/overview.md`
2. `docs/core/overview.md`
3. `docs/shared/overview.md`
4. `docs/integrations/overview.md`
5. `docs/static/ui.md`

### 3-2. 채팅 실행 흐름을 수정할 때

1. `docs/api/chat.md`
2. `docs/core/chat.md`
3. `docs/shared/chat/services/chat_service.md`
4. `docs/shared/chat/services/service_executor.md`
5. `docs/static/ui.md`

### 3-3. 저장소나 인프라를 바꿀 때

1. `docs/shared/chat/repositories/history_repository.md`
2. `docs/integrations/db/overview.md`
3. `docs/setup/env.md`
4. `docs/setup/troubleshooting.md`

## 4. 문서 유지 기준

1. 엔드포인트, DTO 필드, 상태값, 환경 변수 이름은 실제 코드와 같아야 한다.
2. 기본 구현과 선택 확장 구현을 반드시 구분해서 적어야 한다.
3. `request_id` 의미가 바뀌면 `README`, `api`, `shared`, `static` 문서를 함께 수정해야 한다.
4. 환경 변수 설명은 실제 런타임이 읽는 값과 `.env.sample`에 남아 있는 보관용 값을 섞지 않아야 한다.
5. 문서 간 용어는 `session_id`, `request_id`, `context_window`, `assistant_message`, `safeguard_result`로 통일한다.

## 5. 주요 문서

- `docs/api/overview.md`
- `docs/api/chat.md`
- `docs/core/chat.md`
- `docs/shared/chat/overview.md`
- `docs/shared/chat/services/service_executor.md`
- `docs/shared/chat/repositories/history_repository.md`
- `docs/integrations/db/overview.md`
- `docs/setup/env.md`
- `docs/setup/troubleshooting.md`
- `docs/static/ui.md`
