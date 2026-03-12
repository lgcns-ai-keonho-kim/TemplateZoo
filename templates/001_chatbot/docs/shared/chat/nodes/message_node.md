# `nodes/message_node.py` 레퍼런스

`MessageNode`는 상태값을 Enum 메시지로 바꿔 사용자에게 노출할 최종 문구를 선택하는 노드다. 현재는 차단 응답 문구를 결정할 때 사용한다.

## 1. 코드 설명

생성자 핵심 인자:

1. `messages`
2. `selector_key`
3. `output_key`
4. `selector_to_member`
5. `default_member`

매핑 우선순위:

1. `selector_to_member`
2. Enum 멤버명 직접 매칭
3. Enum 값 직접 매칭
4. `default_member`

실패 조건:

1. `messages`가 Enum 클래스가 아니면 `MESSAGE_NODE_CONFIG_INVALID`
2. `selector_key`가 비어 있으면 `MESSAGE_NODE_CONFIG_INVALID`
3. 최종 매핑을 찾지 못하면 `MESSAGE_NODE_MAPPING_NOT_FOUND`

## 2. 유지보수 포인트

1. selector 값과 Enum 멤버명이 완전히 같은 구조가 아니면 `selector_to_member`를 써서 명시적으로 맞추는 편이 안전하다.
2. 이 노드는 문구를 상태 문자열로 확정하므로, 이후 노드는 더 이상 차단 사유를 해석하지 않는다.

## 3. 추가 개발/확장 가이드

1. 차단 사유별 문구를 더 세분화할 때는 Enum을 먼저 확장하고, selector 매핑을 문서와 함께 동기화하는 편이 좋다.
2. 다국어 응답으로 확장하려면 Enum 값 대신 locale별 메시지 공급자를 분리하는 방향이 적합하다.

## 4. 관련 코드

- `src/chatbot/core/chat/nodes/safeguard_message_node.py`
- `src/chatbot/core/chat/const/messages/safeguard.py`
