# Core 개요

`core/agent`는 LangGraph 기반 실행 흐름과 기본 Tool 레지스트리를 제공한다.

## 핵심 구성

1. `graphs`: Agent 그래프 조립
2. `nodes`: safeguard, tool selector, tool execute, retry, response 노드
3. `tools`: 기본 Tool 등록
4. `prompts`: 각 LLM 노드용 프롬프트
5. `models`: 실행 결과/그래프 호환 모델

## 실행 흐름

`safeguard -> tool selector -> tool execute -> retry -> response`

이 그래프는 요청 단위로 독립 실행되며 Tool 선택, 실행, 재시도, 응답 생성을 순서대로 수행한다.
