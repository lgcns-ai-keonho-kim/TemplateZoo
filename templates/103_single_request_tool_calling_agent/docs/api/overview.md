# API 모듈 개요

현재 API 계층은 `1회성 Agent 실행 + 정적 UI + health`만 제공한다.

## 공개 엔드포인트

| 영역 | Method | Path | 상태코드 | 설명 |
| --- | --- | --- | --- | --- |
| Agent | `POST` | `/agent` | `200` | 단일 요청 실행 |
| Health | `GET` | `/health` | `200` | 서버 생존 확인 |
| UI | `GET` | `/ui` | `200` | 정적 단일 요청 화면 |

## 설계 원칙

1. 세션/대화 이력 API는 없다.
2. SSE/폴링/작업 큐 API는 없다.
3. 라우터는 `AgentService` 단일 실행 경계만 주입받는다.
4. `/chat`, `/ui-api/chat/*` 호환 라우트는 제공하지 않는다.
