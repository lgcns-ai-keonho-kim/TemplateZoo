# Core Agent

## 그래프 목적

사용자 요청 1건에 대해 다음 순서로 응답을 만든다.

1. `safeguard`: 입력 안전성 분류
2. `tool_selector_*`: 필요한 Tool 선택
3. `tool_exec`: 선택된 Tool 실행
4. `retry_*`: 실패 Tool 재시도 선택
5. `response_*`: Tool 결과를 바탕으로 최종 응답 생성

## 현재 기본 Tool

| Tool | 목적 |
| --- | --- |
| `get_weather` | 날씨 조회 mock |
| `add_number` | 두 정수 합산 |
| `draft_email` | 이메일 초안 작성 mock |

## 실행 특징

1. 그래프는 여전히 스트림 이벤트를 생성한다.
2. 하지만 외부로 SSE를 내보내지 않고 `AgentService`가 내부에서 직접 집계한다.
3. `blocked` 노드가 선택되면 최종 상태는 `BLOCKED`가 된다.
