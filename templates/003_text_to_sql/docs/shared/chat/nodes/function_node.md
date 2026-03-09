# nodes/function_node.py

외부 함수를 주입받아 실행하는 범용 함수 노드입니다.

## 1. 역할

- 상태 입력을 함수(`fn`)로 처리하고 Mapping 결과를 state patch로 반환합니다.
- 동기(`run`)와 비동기(`arun`) 경로를 모두 지원합니다.
- 현재 core 노드 대부분은 `function_node(...)`로 조립됩니다.

## 2. 주요 인터페이스

| 구성 | 설명 |
| --- | --- |
| `FunctionNode.run` | 동기 실행 |
| `FunctionNode.arun` | 비동기 실행 |
| `function_node(...)` | `FunctionNode` 생성 헬퍼 |

## 3. 실패 경로

| 코드 | 발생 조건 |
| --- | --- |
| `FUNCTION_NODE_CONFIG_INVALID` | `fn`이 callable 아님 / `node_name` 비어 있음 |
| `FUNCTION_NODE_ASYNC_IN_SYNC_RUN` | 동기 경로에서 awaitable 반환 |
| `FUNCTION_NODE_EXECUTION_ERROR` | 주입 함수 내부 예외 |
| `FUNCTION_NODE_OUTPUT_INVALID` | 반환값이 Mapping 아님 |

## 4. 현재 대표 사용 예

- `src/text_to_sql/core/chat/nodes/context_strategy_prepare_node.py`
- `src/text_to_sql/core/chat/nodes/schema_selection_parse_node.py`
- `src/text_to_sql/core/chat/nodes/raw_sql_prepare_node.py`
- `src/text_to_sql/core/chat/nodes/sql_result_collect_node.py`
