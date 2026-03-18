# Shared 개요

`shared`는 Agent 실행에 공통으로 쓰이는 추상체와 유틸을 제공한다.

## 현재 핵심 범위

1. `shared/agent`: 그래프 베이스, 공용 노드, AgentService
2. `shared/logging`: 로거/로그 저장소
3. `shared/exceptions`: 공통 예외

## 보존된 선택 유틸

`shared/runtime`는 `queue`, `worker`, `thread_pool` 유틸을 보존하고 있지만, 현재 기본 `/agent` 런타임 조립 경로에는 포함되지 않는다.
