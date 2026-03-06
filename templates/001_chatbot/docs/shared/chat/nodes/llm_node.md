# `nodes/llm_node.py` 레퍼런스

## 1. 모듈 목적

`LLMNode`는 상태 -> 메시지 변환 -> LLM 호출 -> 토큰/최종 응답 생산 흐름을 공통화한다.

## 2. 핵심 클래스

1. `LLMNode`
- 동기: `run`, `stream`
- 비동기: `arun`, `astream`
- 내부 전략:
  - `stream_tokens=True`: `LLMClient.stream/astream`
  - `stream_tokens=False`: `LLMClient.invoke/ainvoke`

## 3. 입력/출력

1. 생성자 핵심 인자
- `llm_client`, `node_name`, `prompt`
- 상태 키: `output_key`, `user_message_key`, `history_key`

2. 상태 입력 처리
- `user_message_key`가 비어 있으면 실패
- `history_key`가 리스트일 때만 이력 반영
- 프롬프트 변수는 `prompt.input_variables` 기준으로 강제 검증

3. 출력
- `run/arun`: `{output_key: content}`
- `stream/astream`: 토큰 문자열 반복
- 토큰 스트리밍 시 LangGraph custom 이벤트(`event=token`) 방출

## 4. 실패 경로

1. `CHAT_NODE_CONFIG_ERROR`
- 조건: `node_name` 공백, 프롬프트 입력 변수 없음

2. `CHAT_NODE_INPUT_INVALID`
- 조건: 사용자 메시지 누락/공백 또는 상태 정규화 실패

3. `CHAT_NODE_PROMPT_INPUT_INVALID`
- 조건: 프롬프트 변수 누락

4. `CHAT_NODE_PROMPT_FORMAT_ERROR`
- 조건: `prompt.format` 실패

5. `CHAT_STREAM_EMPTY`
- 조건: invoke/stream 결과 텍스트가 비어 있음

## 5. 연계 모듈

1. `src/chatbot/integrations/llm/client.py`
2. `src/chatbot/core/chat/nodes/response_node.py`
3. `nodes/_state_adapter.py`

## 6. 변경 시 영향 범위

1. 스트림 이벤트 스키마를 바꾸면 `BaseChatGraph`/`ServiceExecutor` 이벤트 변환 로직을 함께 수정해야 한다.
2. `history` 변환 로직 변경 시 대화 문맥 품질이 즉시 영향을 받는다.
