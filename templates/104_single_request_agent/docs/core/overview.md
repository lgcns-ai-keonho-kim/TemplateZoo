# Core 개요

`core/agent`는 LangGraph 기반 실행 흐름과 의도 분류 구성을 제공한다.

## 핵심 구성

1. `graphs`: Agent 그래프 조립
2. `nodes`: intent classify, intent prepare, response 노드
3. `prompts`: 각 LLM 노드용 프롬프트
4. `models`: 실행 결과/그래프 호환 모델

## 유지된 흐름

`intent_classify -> intent_prepare -> response`

달라진 점은 `chat session/history` 없이 이 그래프를 요청 1건마다 독립적으로 실행한다는 점이다.
