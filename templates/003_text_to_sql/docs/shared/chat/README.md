# Shared Chat 모듈 문서

`src/text_to_sql/shared/chat`의 공용 실행 요소를 설명하는 문서 허브입니다.

## 1. 읽기 순서

1. `services/service_executor.md`
2. `services/chat_service.md`
3. `repositories/history_repository.md`
4. `runtime/assistant_context.md`
5. `nodes/raw_sql_executor.md`
6. `graph/base_chat_graph.md`
7. `interface/ports.md`

## 2. 현재 문서 구조

```text
docs/shared/chat/
  README.md
  interface/ports.md
  graph/base_chat_graph.md
  memory/session_store.md
  nodes/_state_adapter.md
  nodes/branch_node.md
  nodes/function_node.md
  nodes/llm_node.md
  nodes/message_node.md
  nodes/raw_sql_executor.md
  repositories/history_repository.md
  repositories/schemas/message_schema.md
  repositories/schemas/request_commit_schema.md
  repositories/schemas/session_schema.md
  runtime/assistant_context.md
  runtime/assistant_context_runtime_store.md
  runtime/text_to_sql_runtime_store.md
  services/chat_service.md
  services/service_executor.md
```

## 3. 모듈 인덱스

| 영역 | 문서 | 설명 |
| --- | --- | --- |
| interface | `interface/ports.md` | Graph/Service/Executor 포트 계약 |
| graph | `graph/base_chat_graph.md` | 그래프 실행과 스트림 이벤트 표준화 |
| memory | `memory/session_store.md` | 세션 최근 메시지 캐시 |
| nodes | `nodes/llm_node.md` | 범용 LLM 노드 |
| nodes | `nodes/raw_sql_executor.md` | 읽기 전용 raw SQL 실행기 |
| repositories | `repositories/history_repository.md` | 세션/메시지/요청 커밋 저장소 |
| runtime | `runtime/assistant_context.md` | 직전 assistant 응답 캐시 |
| services | `services/chat_service.md` | 저장소+그래프 결합 서비스 |
| services | `services/service_executor.md` | 큐 워커/SSE 오케스트레이터 |

## 4. 현재 기준 역할 분담

- `shared/chat/services`
  - 세션 저장, 그래프 실행, 이벤트 중계
- `shared/chat/runtime`
  - assistant context, query target registry 같은 런타임 객체 보관
- `shared/chat/nodes`
  - core 노드가 재사용하는 범용 노드와 실행기 제공
- `shared/chat/repositories`
  - SQLite 기반 세션/메시지/요청 커밋 저장
