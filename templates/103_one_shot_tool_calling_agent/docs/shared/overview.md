# Shared 개요

`shared`는 Agent 실행에 공통으로 쓰이는 추상체와 유틸을 제공한다.

## 현재 핵심 범위

1. `shared/agent`: 그래프 베이스, 공용 노드, Tool 레지스트리, AgentService
2. `shared/logging`: 로거/로그 저장소
3. `shared/exceptions`: 공통 예외
4. `shared/runtime`: 범용 런타임 유틸

`shared/runtime`는 현재 Agent 요청 경로에서 직접 쓰이지 않지만, 템플릿 공용 자산으로 남아 있다.
