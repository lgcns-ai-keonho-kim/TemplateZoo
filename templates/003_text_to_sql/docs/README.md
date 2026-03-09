# Text-to-SQL 문서 허브

이 문서는 현재 Raw SQL 기반 Text-to-SQL 구조를 기준으로 문서를 탐색하기 위한 인덱스입니다.

## 1. 먼저 읽을 문서

1. `docs/core/overview.md`
2. `docs/core/chat.md`
3. `docs/api/chat.md`
4. `docs/shared/chat/README.md`
5. `docs/setup/env.md`

## 2. 문서 트리

```text
docs/
  README.md
  api/
    overview.md
    chat.md
    ui.md
    health.md
  core/
    overview.md
    chat.md
  shared/
    overview.md
    chat/
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
    config.md
    const.md
    exceptions.md
    logging.md
    runtime.md
  integrations/
    overview.md
    db/
      README.md
      client.md
      query_target_registry.md
    llm/
      README.md
      client.md
    fs/
      README.md
      file_repository.md
    embedding/
      README.md
      client.md
  setup/
    overview.md
    env.md
    mongodb.md
    filesystem.md
  static/
    ui.md
```

## 3. 코드-문서 매핑

| 코드 경로 | 우선 문서 |
| --- | --- |
| `src/text_to_sql/core/chat` | `docs/core/chat.md` |
| `src/text_to_sql/api/chat` | `docs/api/chat.md` |
| `src/text_to_sql/shared/chat` | `docs/shared/chat/README.md` |
| `src/text_to_sql/static` | `docs/static/ui.md` |
| `src/text_to_sql/api/chat/services/runtime.py` | `docs/setup/env.md` |

## 4. 현재 기준 읽기 포인트

- 전체 흐름: `docs/core/chat.md`
- SSE/요청 처리: `docs/api/chat.md`
- 저장/큐/스트림 오케스트레이션: `docs/shared/chat/README.md`
- 환경 변수와 startup: `docs/setup/env.md`
