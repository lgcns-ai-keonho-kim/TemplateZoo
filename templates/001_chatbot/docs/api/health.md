# API Health 레퍼런스

이 문서는 `/health` 엔드포인트의 현재 구현을 정리한다.

## 1. 현재 인터페이스

관련 코드:

- `src/chatbot/api/health/routers/server.py`
- `src/chatbot/api/main.py`

응답:

```json
{
  "status": "ok"
}
```

| Method | Path | 상태코드 |
| --- | --- | --- |
| `GET` | `/health` | `200` |

## 2. 구현 특징

1. 고정 JSON을 반환하는 liveness 엔드포인트다.
2. DB, LLM, 큐, 이벤트 버퍼 상태를 검사하지 않는다.
3. 외부 의존성 접근이 없어 비용이 낮다.

## 3. 유지보수 포인트

1. 운영 모니터링이 사용할 가능성이 높으므로 응답 구조는 보수적으로 바꿔야 한다.
2. readiness가 필요하면 `/health`를 확장하기보다 별도 경로를 추가하는 편이 안전하다.
3. `status` 필드 제거 또는 이름 변경은 하위 호환을 깨뜨릴 수 있다.

## 4. 관련 문서

- `docs/api/overview.md`
