# Branch Node

## 개요

`src/plan_and_then_execute_agent/shared/chat/nodes/branch_node.py` 구현을 기준으로 현재 동작을 정리한다.

상태값을 정규화해 분기 키를 계산하는 범용 라우터 노드입니다.
`add_conditional_edges` 조건 분기에서 재사용됩니다.

## 주요 설정

1. `selector_key`: 분기 기준 state 키
2. `branch_map`: selector -> branch 매핑
3. `default_branch`: 기본 분기
4. `aliases`: selector 별칭 교정
5. `allowed_selectors` + `fallback_selector`: 허용 토큰 제한
6. `write_normalized_to`: 정규화 결과를 state에 기록

## 출력

- 기본 출력: `{output_key: branch}`
- 선택 출력: `{write_normalized_to: normalized_selector}` 추가

## 관련 문서

- `docs/shared/chat/nodes/message_node.md`
- `docs/shared/chat/nodes/fanout_branch_node.md`
