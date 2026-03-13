# Core 개요

`core/agent`는 LangGraph 기반 실행 흐름과 기본 Tool 레지스트리를 제공한다.

## 핵심 구성

1. `graphs`: Agent 그래프 조립
2. `nodes`: safeguard, tool selector, tool execute, retry, response 노드
3. `tools`: 기본 Tool 등록
4. `prompts`: 각 LLM 노드용 프롬프트
5. `models`: 실행 결과/그래프 호환 모델

## 유지된 흐름

`safeguard -> tool selector -> tool execute -> retry -> response`

달라진 점은 `chat session/history` 없이 이 그래프를 요청 1건마다 독립적으로 실행한다는 점이다.
