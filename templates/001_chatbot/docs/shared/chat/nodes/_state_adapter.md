# `nodes/_state_adapter.py` 레퍼런스

## 1. 모듈 목적

LangGraph 노드 입력 `state`를 `Mapping[str, Any]`로 정규화한다.

## 2. 핵심 함수

1. `coerce_state_mapping(state)`
- 지원 입력:
  - `Mapping`
  - dataclass 인스턴스 (`asdict`)
  - Pydantic 객체 (`model_dump`)
  - 레거시 객체 (`dict` 메서드)
- 반환: 키-값 접근 가능한 `Mapping`

## 3. 입력/출력

1. 입력: `state: object`
2. 출력: `Mapping[str, Any]`

## 4. 실패 경로

1. `CHAT_NODE_INPUT_INVALID`
- 조건: 지원하지 않는 `state` 타입

## 5. 연계 모듈

1. `nodes/llm_node.py`
2. `nodes/branch_node.py`
3. `nodes/message_node.py`
4. `nodes/function_node.py`
5. `nodes/fanout_branch_node.py`

## 6. 변경 시 영향 범위

정규화 규칙이 바뀌면 공용 노드의 입력 타입 경계가 함께 바뀌므로 모든 노드 테스트 케이스를 재검토해야 한다.
