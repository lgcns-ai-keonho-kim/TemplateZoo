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
2. 공개 응답은 요청 1건당 JSON 1건만 반환한다.
3. 라우터는 `AgentService` 단일 실행 경계만 주입받는다.
4. `/agent`는 의도 분류 후 최종 응답만 반환한다.
5. `/chat`, `/ui-api/chat/*` 호환 라우트는 제공하지 않는다.

## 코드 기준 진입점

- Agent 라우터 구현: `src/single_request_agent/api/agent/routers/router.py`
- Health 라우터 구현: `src/single_request_agent/api/health/routers/server.py`
