# `nodes/branch_node.py` 레퍼런스

`BranchNode`는 상태값 하나를 읽어 다음 분기 이름을 계산하는 범용 라우터다. 현재는 `safeguard_result`를 `response` 또는 `blocked`로 바꾸는 데 사용한다.

## 1. 코드 설명

생성자 핵심 인자:

1. `selector_key`
2. `branch_map`
3. `default_branch`
4. `output_key`
5. `aliases`
6. `allowed_selectors`
7. `fallback_selector`
8. `write_normalized_to`

실행 순서:

1. `state`를 `coerce_state_mapping()`으로 정규화
2. `selector_key` 값을 읽고 문자열 정규화
3. `aliases`로 오타/별칭 보정
4. `allowed_selectors` 검증
5. `branch_map`에서 최종 분기 선택
6. 필요하면 정규화된 selector를 다른 키로 다시 기록

## 2. 유지보수 포인트

1. 이 노드는 예외보다 기본 분기 수렴을 우선한다. 따라서 잘못된 입력이 들어와도 `default_branch`로 떨어질 수 있다.
2. `normalize_case=True`가 기본값이므로, 분기 토큰 비교는 대소문자를 무시한다.
3. `write_normalized_to`를 사용하면 후속 노드가 원본 토큰이 아니라 교정된 값을 읽게 된다.

## 3. 추가 개발/확장 가이드

1. LLM 출력 토큰이 흔들리는 경우 먼저 `aliases`와 `allowed_selectors`로 정규화하는 편이, 후속 노드에서 예외 처리하는 것보다 낫다.
2. 분기 종류가 늘어나면 `branch_map`만 늘리지 말고 실제 그래프의 `add_conditional_edges()`도 함께 맞춰야 한다.

## 4. 관련 코드

- `src/chatbot/core/chat/nodes/safeguard_route_node.py`
- `src/chatbot/shared/chat/nodes/_state_adapter.py`
