# Single Request Agent Template

LLM 기반 1회성 Agent 실행 템플릿이다. 기존 대화형 세션 구조를 제거하고, `POST /agent` 한 번으로 의도를 분류한 뒤 최종 결과만 단일 JSON으로 반환하는 형태로 축소되어 있다.

## 빠른 시작

```bash
uv venv .venv
uv sync --group dev
cp .env.sample .env
uv run python -m uvicorn --app-dir src single_request_agent.api.main:app --host 0.0.0.0 --port 8000 --reload
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
| `GET` | `/ui` | 2패널 실행형 UI (`/ui/`로 리다이렉트) |

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
  "output_text": "최종 응답 본문"
}
```

## 지원 의도

- `SUMMARY`: 입력 요약
- `TRANSLATION`: 번역
- `FORMAT_WRITING`: 특정 형식 글쓰기
- `GENERAL`: 일반 질의응답

## 실행 구조

현재 시스템은 `intent_classify -> intent_prepare -> response` 그래프를 사용한다. 특징은 아래와 같다.

1. 세션/대화 이력 저장소를 사용하지 않는다.
2. Tool 호출, 재시도, safeguard 차단 분기를 사용하지 않는다.
3. 작업 큐와 이벤트 버퍼를 사용하지 않는다.
4. `AgentService`가 내부 실행 결과를 직접 집계해 단일 JSON 응답으로 반환한다.

## 코드 기준 진입점

- FastAPI 앱 엔트리 포인트: `src/single_request_agent/api/main.py`
- Agent API 라우터: `src/single_request_agent/api/agent/routers/router.py`
- 정적 UI 진입점: `src/single_request_agent/static/index.html`
- 정적 UI 요청 처리 로직: `src/single_request_agent/static/js/agent/app.js`

## UI 원칙

`/ui`는 채팅형 화면이 아니다. 현재 UI는 아래와 같은 단순한 2패널 구조를 사용한다.

1. 좌측 입력 패널에서 요청서를 작성한다.
2. `Run` 버튼으로 `POST /agent`를 호출한다.
3. 우측 결과 패널 상단에서 `status`, `run_id`를 확인한다.
4. 최종 응답은 결과 영역에 마크다운으로 렌더링된다.
5. 결과가 길어지면 결과 영역 내부에서 스크롤된다.

## 테스트

빠르게 검증한 명령:

```bash
uv run python -m pytest tests/api/test_agent_routes.py tests/core/agent/nodes/test_intent_prepare_node.py
uv run ty check src
```
