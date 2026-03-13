# LLM Node

## 개요

`src/single_request_agent/shared/agent/nodes/llm_node.py` 구현을 기준으로 현재 동작을 정리한다.

프롬프트 + LLM 클라이언트를 주입받아 노드 실행을 공통화합니다.
상태를 메시지로 변환하고 토큰 스트리밍 이벤트를 발행합니다.

## 주요 구성

1. `run()/arun()`: LangGraph 노드 진입점
2. `stream()/astream()`: 토큰 반복자 경로
3. `_build_messages()`: system/history/user 메시지 조립
4. `_format_prompt()`: 프롬프트 변수 바인딩
5. `_build_output()`: 최종 응답 조립

## 이벤트 동작

- 스트리밍 시 `writer({node, event="token", data=text})` 형태로 custom 이벤트를 발행합니다.
- `stream_tokens=False`면 invoke/ainvoke 단건 경로를 사용합니다.

## 실패 경로

- `CHAT_NODE_CONFIG_ERROR`
- `CHAT_NODE_INPUT_INVALID`
- `CHAT_NODE_PROMPT_INPUT_INVALID`
- `CHAT_NODE_PROMPT_FORMAT_ERROR`
- `CHAT_STREAM_EMPTY`

## 관련 문서

- `docs/shared/agent/nodes/_state_adapter.md`
- `docs/shared/agent/services/chat_service.md`
