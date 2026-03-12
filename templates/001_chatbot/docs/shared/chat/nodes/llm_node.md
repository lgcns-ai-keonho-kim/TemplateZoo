# `nodes/llm_node.py` 레퍼런스

`LLMNode`는 상태를 LangChain 메시지로 바꾸고, `LLMClient`를 호출해 토큰 스트림 또는 최종 문자열을 반환하는 범용 노드다. 현재 `response_node`와 `safeguard_node`가 이 구현을 사용한다.

## 1. 코드 설명

생성자 핵심 인자:

1. `llm_client`
2. `node_name`
3. `prompt`
4. `output_key`
5. `user_message_key`
6. `history_key`
7. `stream_tokens`

실행 방식:

1. `stream_tokens=True`이면 `LLMClient.stream/astream`
2. `stream_tokens=False`이면 `LLMClient.invoke/ainvoke`
3. 스트리밍 중에는 `get_stream_writer()`로 `{"node","event":"token","data"}` 이벤트를 전송
4. 최종 결과는 `{output_key: content}`로 반환

실패 조건:

1. `node_name` 공백 또는 프롬프트 입력 변수 없음 -> `CHAT_NODE_CONFIG_ERROR`
2. 사용자 메시지 없음 -> `CHAT_NODE_INPUT_INVALID`
3. 프롬프트 변수 누락 -> `CHAT_NODE_PROMPT_INPUT_INVALID`
4. 프롬프트 포맷 실패 -> `CHAT_NODE_PROMPT_FORMAT_ERROR`
5. 결과 텍스트가 비어 있음 -> `CHAT_STREAM_EMPTY`

## 2. 유지보수 포인트

1. `history_key`가 존재하지 않거나 list가 아니면 히스토리를 조용히 사용하지 않는다. safeguard처럼 단건 분류가 필요할 때 이 특성을 이용한다.
2. `assistant_message` 외 다른 출력 키를 쓰는 노드는 상위 서비스가 그 의미를 이해하는지 함께 봐야 한다.
3. 토큰 이벤트 스키마는 `BaseChatGraph`와 `ServiceExecutor`가 함께 기대하는 형식이다.

## 3. 추가 개발/확장 가이드

1. 새 LLM 노드를 추가할 때는 상속보다 조립(`LLMNode(...)`) 방식이 현재 구조와 잘 맞는다.
2. 히스토리 가공 규칙을 바꾸고 싶다면 `_history_to_langchain()`만 최소 수정하고, 상위 서비스의 문맥 선택 로직과 역할을 혼동하지 않는 것이 좋다.

## 4. 관련 코드

- `src/chatbot/integrations/llm/client.py`
- `src/chatbot/core/chat/nodes/response_node.py`
- `src/chatbot/core/chat/nodes/safeguard_node.py`
