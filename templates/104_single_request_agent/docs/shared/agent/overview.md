# Shared Agent 개요

`shared/agent`는 코어 그래프가 직접 재사용하는 공용 구현을 제공한다.

## 주요 구성

| 영역 | 역할 |
| --- | --- |
| `graph` | LangGraph 공통 실행 래퍼 |
| `nodes` | LLMNode, FunctionNode 등 범용 노드 |
| `services` | `AgentService` 단건 실행 집계 |

## AgentService 역할

`AgentService`는 다음 작업만 수행한다.

1. 요청 1건에 대해 `run_id` 생성
2. 그래프 스트림 이벤트 직접 소비
3. `token`, `assistant_message` 집계
4. 최종 `output_text`, `status` 반환

세션 저장, 메시지 저장, SSE 전송, 작업 큐 소비는 하지 않는다.
