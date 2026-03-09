# Core 모듈 가이드

`src/text_to_sql/core`는 채팅 그래프, 노드, 프롬프트, 상태 타입을 포함하는 도메인 계층입니다.

## 1. 책임

| 경로 | 책임 | 주요 파일 |
| --- | --- | --- |
| `src/text_to_sql/core/chat/models` | 세션/메시지 도메인 모델 | `entities.py` |
| `src/text_to_sql/core/chat/const` | 저장소/페이지네이션/분기 상수 | `settings.py`, `routes.py` |
| `src/text_to_sql/core/chat/prompts` | schema selection, raw SQL generation, response 프롬프트 | `schema_selection_prompt.py`, `raw_sql_generation_prompt.py`, `chat_prompt.py` |
| `src/text_to_sql/core/chat/nodes` | safeguard, 컨텍스트 전략, raw SQL 실행, 응답 조립 | `safeguard_node.py`, `context_strategy_*`, `raw_sql_*`, `response_node.py` |
| `src/text_to_sql/core/chat/graphs` | LangGraph 조립 | `chat_graph.py` |
| `src/text_to_sql/core/chat/state` | 그래프 상태 타입 | `graph_state.py` |
| `src/text_to_sql/core/chat/utils` | allowlist 로드, introspection, 매퍼 | `table_allowlist_loader.py`, `schema_introspection.py` |

## 2. 현재 실행 관점 핵심 포인트

1. 그래프 진입점은 `safeguard`입니다.
2. startup에서 allowlist 로드와 schema introspection이 먼저 완료되어 `schema_snapshot`이 정적 입력으로 주입됩니다.
3. `context_strategy`는 `REUSE_LAST_ASSISTANT`, `USE_METADATA`, `USE_SQL` 중 하나를 결정합니다.
4. 새 SQL이 필요한 경우 `schema selection -> raw SQL generation -> raw SQL execution` 순서로 진행합니다.
5. query target registry는 startup에 등록되지만, 실제 DB 연결은 첫 조회 시점에 lazy connect 됩니다.
6. SQL 성공 결과는 `answer_source_meta`로 저장되어 후속 설명 질문에 재사용됩니다.
7. 최종 응답은 모든 경로에서 `assistant_message`로 종료됩니다.

## 3. 읽기 순서

1. `src/text_to_sql/core/chat/graphs/chat_graph.py`
2. `src/text_to_sql/core/chat/state/graph_state.py`
3. `src/text_to_sql/core/chat/nodes/context_strategy_*`
4. `src/text_to_sql/core/chat/nodes/schema_selection_*`
5. `src/text_to_sql/core/chat/nodes/raw_sql_*`
6. `src/text_to_sql/core/chat/nodes/sql_result_collect_node.py`
7. `src/text_to_sql/core/chat/nodes/response_node.py`
