# State Adapter

## 개요

`src/one_shot_agent/shared/agent/nodes/_state_adapter.py` 구현을 기준으로 현재 동작을 정리한다.

LangGraph 노드 입력을 `Mapping[str, Any]`로 정규화합니다.
노드 구현에서 타입 분기 코드를 반복하지 않도록 공통 경계를 제공합니다.

## 핵심 함수

- `coerce_state_mapping(state)`: Mapping/dataclass/Pydantic 입력을 dict 기반 매핑으로 변환

## 지원 입력

1. `Mapping`
2. dataclass 인스턴스
3. `model_dump()` 제공 객체
4. `dict()` 제공 객체

## 실패 경로

- `CHAT_NODE_INPUT_INVALID`: 지원하지 않는 state 타입

## 관련 문서

- `docs/shared/agent/nodes/llm_node.md`
- `docs/shared/agent/nodes/message_node.md`
- `docs/shared/agent/nodes/branch_node.md`
