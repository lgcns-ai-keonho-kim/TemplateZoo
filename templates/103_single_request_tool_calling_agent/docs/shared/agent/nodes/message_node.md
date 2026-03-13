# Message Node

## 개요

`src/single_request_tool_agent/shared/agent/nodes/message_node.py` 구현을 기준으로 현재 동작을 정리한다.

분류 결과(selector)를 Enum 메시지로 변환합니다.
상태값을 사용자 응답 문구로 안정적으로 매핑하는 용도로 사용됩니다.

## 주요 설정

1. `messages`: 메시지 Enum 클래스
2. `selector_key`: selector 입력 키
3. `selector_to_member`: 별칭 매핑
4. `default_member`: 매핑 실패 시 기본 멤버
5. `output_key`: 기본 `assistant_message`

## 매핑 우선순위

1. `selector_to_member`
2. Enum member name 매칭
3. Enum member value 매칭
4. `default_member`

## 실패 경로

- `MESSAGE_NODE_CONFIG_INVALID`
- `MESSAGE_NODE_MAPPING_NOT_FOUND`

## 관련 문서

- `docs/shared/agent/nodes/branch_node.md`
