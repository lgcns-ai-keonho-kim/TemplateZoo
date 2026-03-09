# graph/base_chat_graph.py

Builder 주입형 그래프 실행 공통체로, invoke/stream 이벤트 처리 규칙을 표준화한다.

## 1. 역할

- 그래프 컴파일과 실행(`invoke`, `ainvoke`)을 공통화한다.
- LangGraph `custom`, `updates` 이벤트를 `{node,event,data}` 형식으로 정규화한다.
- `stream_node` 정책으로 노드별 허용 이벤트를 필터링한다.

## 2. 핵심 구성

| 구성 | 설명 |
| --- | --- |
| `DefaultChatGraphInput` | 기본 입력 모델(`session_id`, `user_message`, `history`) |
| `BaseChatGraph.compile` | builder를 실제 실행 그래프로 컴파일 |
| `BaseChatGraph.set_static_input` | 모든 요청에 병합되는 정적 state 주입 |
| `BaseChatGraph.stream_events` | 동기 스트리밍 이벤트 변환 |
| `BaseChatGraph.astream_events` | 비동기 스트리밍 이벤트 변환 |

## 3. 실패 경로

| 코드 | 발생 조건 |
| --- | --- |
| `CHAT_STREAM_EMPTY` | invoke/ainvoke 결과에 `assistant_message`가 비어 있음 |
| `CHAT_STREAM_NODE_INVALID` | `stream_node` 설정값이 문자열/시퀀스 규칙을 만족하지 않음 |

## 4. 연관 모듈

- `src/text_to_sql/core/chat/graphs/chat_graph.py`
- `src/text_to_sql/shared/chat/interface/ports.py`
