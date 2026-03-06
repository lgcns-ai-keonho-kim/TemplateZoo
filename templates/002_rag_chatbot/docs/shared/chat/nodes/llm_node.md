# LLM Node

이 문서는 `src/rag_chatbot/shared/chat/nodes/llm_node.py`를 설명한다.

## 1. 목적

- 프롬프트/LLM/출력 키를 주입받아 공통 LLM 노드 실행을 제공한다.
- 토큰 스트리밍과 최종 출력 생성을 공통화한다.

## 2. 핵심 입력

| 입력 | 설명 |
| --- | --- |
| `llm_client` | 모델 호출 클라이언트 |
| `node_name` | 노드 식별자(이벤트 node 값) |
| `prompt` | 시스템 프롬프트 템플릿 |
| `output_key` | 결과 기록 키(기본 `assistant_message`) |
| `user_message_key` | 사용자 메시지 키 |
| `history_key` | 대화 이력 키 |
| `stream_tokens` | 토큰 스트리밍 사용 여부 |

## 3. 주요 메서드

1. `run`, `arun`: 노드 실행 후 `{output_key: text}` 반환
2. `stream`, `astream`: 토큰 iterator/async iterator 반환

## 4. 스트리밍 동작

- `stream_tokens=True`이면 `llm_client.stream/astream` 경로를 사용한다.
- 토큰마다 LangGraph custom stream writer로 `{node, event="token", data}` 이벤트를 전송한다.
- 최종 출력 텍스트가 비어 있으면 예외를 발생시킨다.

## 5. 실패/예외 포인트

- 빈 `node_name`: `CHAT_NODE_CONFIG_ERROR`
- 프롬프트 입력 변수 없음: `CHAT_NODE_CONFIG_ERROR`
- 입력 state 타입 부적합: `CHAT_NODE_INPUT_INVALID`

## 6. 관련 문서

- `docs/shared/chat/nodes/_state_adapter.md`
- `docs/shared/chat/graph/base_chat_graph.md`
- `docs/core/chat.md`
