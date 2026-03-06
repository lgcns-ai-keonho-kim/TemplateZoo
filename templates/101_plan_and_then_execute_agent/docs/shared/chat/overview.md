# Shared Chat 개요

이 문서는 `src/plan_and_then_execute_agent/shared/chat` 모듈을 파일 단위로 탐색하기 위한 허브입니다.
`__init__.py`는 제외하고 실제 동작 파일만 문서화합니다.

## 1. 디렉터리 구조

```text
docs/shared/chat/
  overview.md
  interface/
    ports.md
  graph/
    base_chat_graph.md
  memory/
    session_store.md
  nodes/
    _state_adapter.md
    _tool_exec_support.md
    branch_node.md
    fanout_branch_node.md
    function_node.md
    llm_node.md
    message_node.md
    tool_exec_node.md
  repositories/
    history_repository.md
    schemas/
      message_schema.md
      request_commit_schema.md
      session_schema.md
  services/
    _service_executor_support.md
    chat_service.md
    service_executor.md
  tools/
    prompt_payload.md
    registry.md
    types.md
```

## 2. 파일 인덱스

| 코드 파일 | 문서 |
| --- | --- |
| `shared/chat/interface/ports.py` | `docs/shared/chat/interface/ports.md` |
| `shared/chat/graph/base_chat_graph.py` | `docs/shared/chat/graph/base_chat_graph.md` |
| `shared/chat/memory/session_store.py` | `docs/shared/chat/memory/session_store.md` |
| `shared/chat/nodes/_state_adapter.py` | `docs/shared/chat/nodes/_state_adapter.md` |
| `shared/chat/nodes/_tool_exec_support.py` | `docs/shared/chat/nodes/_tool_exec_support.md` |
| `shared/chat/nodes/branch_node.py` | `docs/shared/chat/nodes/branch_node.md` |
| `shared/chat/nodes/fanout_branch_node.py` | `docs/shared/chat/nodes/fanout_branch_node.md` |
| `shared/chat/nodes/function_node.py` | `docs/shared/chat/nodes/function_node.md` |
| `shared/chat/nodes/llm_node.py` | `docs/shared/chat/nodes/llm_node.md` |
| `shared/chat/nodes/message_node.py` | `docs/shared/chat/nodes/message_node.md` |
| `shared/chat/nodes/tool_exec_node.py` | `docs/shared/chat/nodes/tool_exec_node.md` |
| `shared/chat/repositories/history_repository.py` | `docs/shared/chat/repositories/history_repository.md` |
| `shared/chat/repositories/schemas/message_schema.py` | `docs/shared/chat/repositories/schemas/message_schema.md` |
| `shared/chat/repositories/schemas/request_commit_schema.py` | `docs/shared/chat/repositories/schemas/request_commit_schema.md` |
| `shared/chat/repositories/schemas/session_schema.py` | `docs/shared/chat/repositories/schemas/session_schema.md` |
| `shared/chat/services/_service_executor_support.py` | `docs/shared/chat/services/_service_executor_support.md` |
| `shared/chat/services/chat_service.py` | `docs/shared/chat/services/chat_service.md` |
| `shared/chat/services/service_executor.py` | `docs/shared/chat/services/service_executor.md` |
| `shared/chat/tools/prompt_payload.py` | `docs/shared/chat/tools/prompt_payload.md` |
| `shared/chat/tools/registry.py` | `docs/shared/chat/tools/registry.md` |
| `shared/chat/tools/types.py` | `docs/shared/chat/tools/types.md` |

## 3. 실행 흐름 기준 읽기 순서

1. `interface/ports.md`
2. `graph/base_chat_graph.md`
3. `services/chat_service.md`
4. `services/service_executor.md`
5. `repositories/history_repository.md`
6. `nodes/tool_exec_node.md`
7. `tools/registry.md`
