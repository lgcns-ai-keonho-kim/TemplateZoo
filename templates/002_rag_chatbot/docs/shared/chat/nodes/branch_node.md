# Branch Node

이 문서는 `src/rag_chatbot/shared/chat/nodes/branch_node.py`를 설명한다.

## 1. 목적

- 상태 값 기반으로 분기 키를 계산해 conditional edge 라우팅 값을 생성한다.

## 2. 핵심 입력

| 입력 | 설명 |
| --- | --- |
| `selector_key` | 분기 기준 상태 키 |
| `branch_map` | selector -> branch 매핑 |
| `default_branch` | 미매핑 기본 분기 |
| `aliases` | 별칭 정규화 매핑 |
| `allowed_selectors` | 허용 selector 집합 |
| `fallback_selector` | 비허용 값 대체 selector |

## 3. 주요 메서드

- `run(state, config=None) -> dict[str, str]`

출력:

1. 기본 출력 키(`output_key`)에 분기 결과를 기록
2. 선택적으로 `write_normalized_to` 키에 정규화 selector를 기록

## 4. 분기 계산 순서

1. `selector_key` 읽기
2. trim/대소문자 정규화
3. alias 적용
4. 허용값 검증 및 fallback 적용
5. `branch_map` 조회 또는 `default_branch` 적용

## 5. 관련 문서

- `docs/shared/chat/nodes/_state_adapter.md`
- `docs/core/chat.md`
