# API Health

헬스체크 API의 역할, 인터페이스, 확장 시 주의점을 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 코드 |
| --- | --- | --- |
| 헬스체크 | 프로세스의 기본 생존 여부를 확인하는 경로 | `GET /health` |
| Liveness | 프로세스가 살아 있는지 확인하는 관점 | `src/text_to_sql/api/health/routers/server.py` |
| Readiness | 외부 의존성 포함 준비 상태 확인 관점 | 별도 라우터로 확장 필요 |

## 2. 관련 스크립트

| 파일 | 역할 |
| --- | --- |
| `src/text_to_sql/api/health/routers/server.py` | `/health` 라우터 정의 |
| `src/text_to_sql/api/main.py` | health 라우터 앱 등록 |

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

1. 응답은 고정 JSON이다.
2. DB, LLM, Queue 연결 상태는 검사하지 않는다.
3. 빠른 응답이 목적이므로 고비용 로직을 넣지 않는다.

## 4. 관련 문서

- `docs/api/overview.md`
- `docs/api/chat.md`
