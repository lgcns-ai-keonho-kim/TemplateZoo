# `nodes/branch_node.py` 레퍼런스

## 1. 모듈 목적

`BranchNode`는 상태값을 읽어 분기 키를 계산하는 범용 라우터다.

## 2. 핵심 클래스

1. `BranchNode`
- `selector_key`: 분기 기준 상태 키
- `branch_map`: selector -> branch 매핑
- `default_branch`: 미매칭 시 기본 분기
- `aliases`: 오타/별칭 정규화
- `allowed_selectors` + `fallback_selector`: 허용 토큰 강제
- `write_normalized_to`: 정규화된 selector 재기록 키

## 3. 입력/출력

1. `run(state, config=None)`
- 입력: 임의 상태 객체 (`coerce_state_mapping` 적용)
- 출력: `{output_key: branch}`
- 옵션: `write_normalized_to` 지정 시 `{write_normalized_to: normalized}` 추가

## 4. 실패 경로

- 명시적 예외를 거의 발생시키지 않고 `default_branch`로 수렴한다.
- 입력 정규화 실패는 `_state_adapter`의 `CHAT_NODE_INPUT_INVALID`가 전파된다.

## 5. 연계 모듈

1. `src/chatbot/core/chat/nodes/safeguard_route_node.py`
2. `nodes/message_node.py`

## 6. 변경 시 영향 범위

1. `aliases`/`allowed_selectors` 변경 시 분기 방향이 즉시 달라짐
2. `output_key` 변경 시 graph `add_conditional_edges`와 키 일치 확인 필요
