# Interface Ports

## 개요

`src/one_shot_tool_calling_agent/shared/agent/interface/ports.py` 구현을 기준으로 현재 동작을 정리한다.

`shared/agent` 계층의 포트(Protocol) 계약을 정의합니다.
현재는 `BaseAgentGraph`와 `AgentService`가 이 계약을 중심으로 조립됩니다.

## 주요 타입

1. `StreamNodeConfig`: 스트림 노드 정책 타입 별칭
2. `GraphPort`: 그래프 컴파일/실행/스트림 인터페이스

## 인터페이스 경계

- `GraphPort`는 `invoke/ainvoke`와 `stream_events/astream_events`를 모두 제공합니다.
- 현재 기본 `/agent` 라우터는 `AgentService`를 직접 사용하며, `GraphPort`의 이벤트는 내부 집계 용도로만 사용합니다.

## 관련 문서

- `docs/shared/agent/graph/base_agent_graph.md`
