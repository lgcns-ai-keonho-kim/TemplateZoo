# nodes/branch_node.py

상태값을 정규화해 분기 키를 계산하는 범용 라우팅 노드다.

## 1. 역할

- `selector_key` 값을 읽어 `branch_map`으로 분기명을 계산한다.
- 별칭(`aliases`), 허용 selector(`allowed_selectors`), fallback selector를 조합해 분기 안정성을 높인다.

## 2. 주요 메서드

| 메서드 | 설명 |
| --- | --- |
| `run` | LangGraph 진입점 |
| `_run` | selector 정규화 및 branch 계산 |
| `_match_allowed_selector` | prefix 기반 허용 토큰 복원 |

## 3. 출력 형태

- 기본 출력: `{output_key: branch}`
- 옵션 `write_normalized_to` 사용 시 정규화 selector를 함께 기록한다.

## 4. 관련 코드

- `src/text_to_sql/core/chat/nodes/safeguard_route_node.py`
- `nodes/_state_adapter.py`
