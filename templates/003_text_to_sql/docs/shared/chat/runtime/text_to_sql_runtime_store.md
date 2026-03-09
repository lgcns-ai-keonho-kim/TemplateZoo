# runtime/text_to_sql_runtime_store.py

`QueryTargetRegistry`를 전역으로 공유하는 런타임 상태 모듈입니다.

## 1. 역할

- `QueryTargetRegistry` 인스턴스를 모듈 전역으로 보관합니다.
- schema selection, raw SQL 준비, raw SQL 실행 노드가 동일 registry를 참조할 수 있게 합니다.

## 2. 공개 함수

| 함수 | 설명 |
| --- | --- |
| `set_query_target_registry` | registry 설정 |
| `get_query_target_registry` | registry 조회 |
| `clear_query_target_registry` | registry 제거 |

## 3. 사용 위치

- 조립: `src/text_to_sql/api/chat/services/runtime.py`
- 노드: `src/text_to_sql/core/chat/nodes/schema_selection_prepare_node.py`
- 노드: `src/text_to_sql/core/chat/nodes/raw_sql_prepare_node.py`
- 노드: `src/text_to_sql/core/chat/nodes/raw_sql_execute_node.py`
