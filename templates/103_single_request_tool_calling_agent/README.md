# Single Request Tool Agent Template

LLM 기반 1회성 Agent 실행 템플릿이다. 기존 `chat + session + SSE` 구조를 공개 API와 기본 실행 경로에서 제거하고, `POST /agent` 한 번으로 최종 응답과 Tool 결과를 함께 반환하는 형태로 축소되어 있다.

현재 런타임 코드 루트는 `src/single_request_tool_agent`다.

## 빠른 시작

```bash
uv venv .venv
uv sync --group dev
cp .env.sample .env
PYTHONPATH=src uv run uvicorn single_request_tool_agent.api.main:app --host 0.0.0.0 --port 8000 --reload
```

필수 환경 변수 예시:

```env
ENV=local
LOG_STDOUT=1

GEMINI_MODEL=gemini-3.1-flash-lite-preview
GEMINI_PROJECT=your-gcp-project-id
GEMINI_API_KEY=

AGENT_REQUEST_TIMEOUT_SECONDS=180
```

## 공개 경로

| Method | Path | 설명 |
| --- | --- | --- |
| `POST` | `/agent` | 1회성 Agent 요청 실행 |
| `GET` | `/health` | 서버 상태 확인 |
| `GET` | `/ui` | 단일 요청 정적 UI |

## 요청/응답 계약

### 요청

```json
{
  "request": "김대리에게 일정 조율 메일 초안 작성해줘."
}
```

### 응답

```json
{
  "run_id": "c4f1...",
  "status": "COMPLETED",
  "output_text": "최종 응답 본문",
  "tool_results": [
    {
      "tool_name": "draft_email",
      "status": "SUCCESS",
      "output": {
        "recipient": "김대리",
        "subject": "일정 조율",
        "body": "...",
        "tone": "정중한",
        "mock": true
      },
      "error_message": null,
      "attempt": 1
    }
  ]
}
```

`status`가 `BLOCKED`이면 safeguard에 의해 차단된 응답이다.

## 기본 Tool

- `get_weather`: 고정 응답 기반 날씨 조회 mock
- `add_number`: 두 정수 합산
- `draft_email`: 이메일 초안 작성 mock

## 실행 구조

현재 시스템은 `safeguard -> tool selector -> tool execute -> retry -> response` 그래프를 유지한다. 달라진 점은 아래와 같다.

1. 기본 런타임 경로에서는 세션/대화 이력 저장소를 사용하지 않는다.
2. 기본 런타임 경로에서는 JobQueue/EventBuffer/SSE를 사용하지 않는다.
3. `AgentService`가 그래프 이벤트를 직접 집계해 단일 JSON 응답으로 반환한다.

## 테스트

빠르게 검증한 명령:

```bash
uv run pytest tests/api/test_agent_routes.py tests/core/agent/tools/test_draft_email.py tests/core/agent/nodes/test_tool_call_selection.py tests/shared/agent/tools/test_registry.py tests/shared/agent/tools/test_schema_validator.py
uv run pytest tests/e2e/test_agent_api_server_e2e.py
uv run ty check src
```
