# API Agent

`/agent` 단일 엔드포인트 계약을 정리한다.

## 요청

- Method: `POST`
- Path: `/agent`
- Request Body:

```json
{
  "request": "서울 날씨 알려줘."
}
```

검증 규칙:

1. `request`는 최소 1자 이상이어야 한다.
2. 비어 있으면 `422` 또는 `AGENT_REQUEST_EMPTY`가 반환된다.

## 응답

```json
{
  "run_id": "9dbe...",
  "status": "COMPLETED",
  "output_text": "서울은 현재 맑음입니다.",
  "tool_results": [
    {
      "tool_name": "get_weather",
      "status": "SUCCESS",
      "output": {
        "data": {
          "country": "South Korea",
          "region": "Seoul"
        }
      },
      "error_message": null,
      "attempt": 1
    }
  ]
}
```

## 상태 의미

| 값 | 의미 |
| --- | --- |
| `COMPLETED` | 정상 완료 |
| `BLOCKED` | safeguard 차단 |

## 오류 응답

| 코드 | HTTP |
| --- | --- |
| `AGENT_REQUEST_EMPTY` | `400` |
| `AGENT_REQUEST_TIMEOUT` | `504` |
| 기타 내부 예외 | `500` |
