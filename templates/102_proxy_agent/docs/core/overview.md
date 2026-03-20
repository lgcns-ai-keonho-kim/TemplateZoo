# Core 모듈 개요

`src/tool_proxy_agent/core` 계층의 책임 경계와 실행 구조를 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 코드 |
| --- | --- | --- |
| 도메인 모델 | 세션/메시지 같은 핵심 데이터 구조 | `src/tool_proxy_agent/core/chat/models/entities.py` |
| 그래프 | 노드 실행 순서를 정의한 워크플로우 | `src/tool_proxy_agent/core/chat/graphs/chat_graph.py` |
| 노드 | 그래프에서 단위 작업을 수행하는 실행 컴포넌트 | `src/tool_proxy_agent/core/chat/nodes/*.py` |
| 상태 | 노드 사이를 흐르는 공통 키 집합 | `src/tool_proxy_agent/core/chat/state/graph_state.py` |
| 프롬프트 | LLM 노드에 주입되는 텍스트 템플릿 | `src/tool_proxy_agent/core/chat/prompts/*.py` |
| 스트림 노드 정책 | 어떤 노드의 어떤 이벤트를 외부에 노출할지 정한 규칙 | `chat_graph.py`의 `stream_node` |

## 2. 디렉터리와 관련 스크립트

| 경로 | 책임 | 주요 스크립트 |
| --- | --- | --- |
| `src/tool_proxy_agent/core/chat/models` | 도메인 엔티티 | `entities.py` |
| `src/tool_proxy_agent/core/chat/const` | 저장/조회/컨텍스트 상수 | `settings.py`, `messages/safeguard.py` |
| `src/tool_proxy_agent/core/chat/prompts` | 노드 프롬프트 템플릿 | `safeguard_prompt.py`, `planner_prompt.py`, `replan_prompt.py`, `chat_prompt.py` |
| `src/tool_proxy_agent/core/chat/nodes` | safeguard + planner + execute + replan + response 조립 | `safeguard_node.py`, `planner_*`, `execute_*`, `replan_*`, `response_node.py` |
| `src/tool_proxy_agent/core/chat/graphs` | LangGraph 조립과 stream 정책 | `chat_graph.py` |
| `src/tool_proxy_agent/core/chat/state` | 그래프 상태 타입 | `graph_state.py` |
| `src/tool_proxy_agent/core/chat/utils` | 도메인 문서 매퍼 | `mapper.py` |

연동 스크립트:

1. `src/tool_proxy_agent/shared/chat/graph/base_chat_graph.py`
2. `src/tool_proxy_agent/shared/chat/services/chat_service.py`
3. `src/tool_proxy_agent/shared/chat/services/service_executor.py`
4. `src/tool_proxy_agent/api/chat/services/runtime.py`

## 3. 의존성 경계

핵심 규칙:

1. `core`는 FastAPI 타입에 의존하지 않는다.
2. HTTP DTO는 `api/*/models`에 둔다.
3. 외부 시스템 호출은 `integrations`와 `shared`를 경유한다.

의존 흐름:

```text
core -> shared -> api
core -> integrations
```

## 4. 실행 관점 핵심 포인트

1. 그래프 진입점은 `safeguard`다.
2. Planner가 ToolRegistry 스펙을 기반으로 실행 계획(JSON)을 생성한다.
3. Execute 단계는 배치 단위 fan-out으로 Tool을 실행하고 실패 시 Replan으로 분기한다.
4. 최종 응답 키는 모든 경로에서 `assistant_message`다.
5. 스트림 노출 이벤트는 `stream_node`로 제한된다.

## 7. 관련 문서

- `docs/core/chat.md`
- `docs/api/chat.md`
- `docs/shared/chat/overview.md`
