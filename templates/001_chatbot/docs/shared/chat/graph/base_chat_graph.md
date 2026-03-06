# `graph/base_chat_graph.py` 레퍼런스

## 1. 모듈 목적

`BaseChatGraph`는 Builder 주입 방식으로 LangGraph 컴파일/실행을 공통화한다.

- 입력 모델 검증
- 동기/비동기 실행 (`invoke`, `ainvoke`)
- 스트림 이벤트 표준화 (`stream_events`, `astream_events`)
- `stream_node` 정책 기반 이벤트 필터링

## 2. 핵심 타입

1. `DefaultChatGraphInput`
- 기본 입력 모델
- 필드: `session_id`, `user_message`, `history`, `assistant_message`

2. `BaseChatGraph`
- `builder.compile()`로 그래프 객체를 만들고 내부에 보관
- 실행 시 `configurable.thread_id`를 `session_id`로 강제 보정

## 3. 입력/출력

1. `invoke/ainvoke`
- 입력: `session_id`, `user_message`, `history`, `config`
- 출력: 최종 `assistant_message` 문자열

2. `stream_events/astream_events`
- 입력: 위와 동일
- 출력: `{"node", "event", "data"}` 형태 이벤트 반복자
- `mode=custom`, `mode=updates`를 하나의 표준 이벤트로 병합

3. `set_stream_node`
- 입력 타입: `StreamNodeConfig = Mapping[str, str | Sequence[str]]`
- 내부 표현: `dict[str, set[str]]`

## 4. 실패 경로

1. `CHAT_STREAM_EMPTY`
- 조건: `invoke/ainvoke` 결과에 `assistant_message`가 비어 있음

2. `CHAT_STREAM_NODE_INVALID`
- 조건: `stream_node` 값이 문자열/시퀀스가 아닌 타입

## 5. 연계 모듈

1. 상위 조립: `src/chatbot/core/chat/graphs/chat_graph.py`
2. 포트 타입: `src/chatbot/shared/chat/interface/ports.py`
3. 예외 모델: `src/chatbot/shared/exceptions/*`

## 6. 변경 시 영향 범위

1. 이벤트 포맷 변경 시 `ServiceExecutor._normalize_graph_event()`와 함께 확인
2. 입력 모델 필드 변경 시 core graph 상태 키와 일치 여부 확인
3. `stream_node` 정책 변경 시 SSE 노출 이벤트가 줄거나 사라질 수 있음
