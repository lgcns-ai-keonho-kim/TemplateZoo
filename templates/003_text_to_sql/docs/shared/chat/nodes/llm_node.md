# nodes/llm_node.py

LLM 호출/프롬프트 포맷/토큰 스트리밍을 공통화하는 범용 노드다.

## 1. 역할

- state를 메시지 배열로 변환해 `LLMClient`에 전달한다.
- 스트리밍 모드에서는 token 이벤트를 writer로 전달하고, 최종 결과를 output key로 반환한다.

## 2. 주요 인터페이스

| 메서드 | 설명 |
| --- | --- |
| `run`, `arun` | LangGraph 노드 실행 엔트리 |
| `stream`, `astream` | 토큰 단위 스트림 반환 |
| `_build_messages` | 시스템 프롬프트 + history + 사용자 메시지 조립 |
| `_format_prompt` | PromptTemplate 입력 변수 검증/포맷 |

## 3. 실패 경로

| 코드 | 발생 조건 |
| --- | --- |
| `CHAT_NODE_CONFIG_ERROR` | `node_name` 비어 있음, prompt input variable 없음 |
| `CHAT_NODE_INPUT_INVALID` | 사용자 입력 키가 비어 있음 |
| `CHAT_NODE_PROMPT_INPUT_INVALID` | 프롬프트 변수 누락 |
| `CHAT_NODE_PROMPT_FORMAT_ERROR` | prompt format 예외 |
| `CHAT_STREAM_EMPTY` | invoke/stream 결과 텍스트가 비어 있음 |

## 4. 이벤트 출력 규칙

- 스트리밍 시 writer로 `{node, event="token", data=<text>}` 전송
- `_build_output`은 `{output_key: content}` 형태를 보장

## 5. 관련 코드

- `src/text_to_sql/integrations/llm/client.py`
- `src/text_to_sql/core/chat/nodes/response_node.py`
