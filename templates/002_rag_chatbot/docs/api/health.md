# API Health 가이드

이 문서는 헬스체크 API의 역할, 인터페이스, 확장 시 주의점을 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 코드 |
| --- | --- | --- |
| 헬스체크 | 프로세스의 기본 생존 여부를 확인하는 경로 | `GET /health` |
| Liveness | 프로세스가 살아 있는지 확인하는 관점 | `src/rag_chatbot/api/health/routers/server.py` |
| Readiness | 외부 의존성 포함 준비 상태 확인 관점 | 별도 라우터로 확장 필요 |

## 2. 관련 스크립트

| 파일 | 역할 |
| --- | --- |
| `src/rag_chatbot/api/health/routers/server.py` | `/health` 라우터 정의 |
| `src/rag_chatbot/api/main.py` | health 라우터 앱 등록 |

## 3. 인터페이스

- Method: `GET`
- Path: `/health`
- Status: `200 OK`
- Response:

```json
{
  "status": "ok"
}
```

구현 포인트:

1. 현재 응답은 고정 JSON이다.
2. DB, LLM, Queue 연결 상태는 검사하지 않는다.
3. 빠른 응답이 목적이므로 고비용 로직을 넣지 않는다.

## 4. 운영 확인 절차

1. 서버 기동 직후 `GET /health`가 `200`인지 확인한다.
2. 로드밸런서 헬스체크 경로를 `/health`로 고정한다.
3. 장애 분석 시 `/health` 성공 여부와 `/chat` 실패를 분리해서 판단한다.

## 5. 확장 절차

## 5-1. Readiness 경로 추가

1. `src/rag_chatbot/api/health/routers`에 readiness 라우터 파일을 추가한다.
2. `src/rag_chatbot/api/main.py`에 라우터 등록을 추가한다.
3. 기존 `/health` 응답 형식은 유지한다.

## 5-2. 응답 필드 확장

1. 기존 `status` 필드를 삭제하지 않는다.
2. 새 필드는 하위 호환 형태로 추가한다.
3. 모니터링 시스템 파싱 규칙과 동시에 반영한다.

## 6. 소스 매칭 점검 항목

1. `/health` 라우터가 앱에 등록되어 있는가
2. 상태코드가 `200`으로 고정되어 있는가
3. 응답 키가 `status`로 유지되는가
4. 문서 경로와 실제 라우터 파일 경로가 일치하는가

## 7. 관련 문서

- `docs/api/overview.md`
- `docs/api/chat.md`
