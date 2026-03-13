# Base Chat Graph

## 개요

`src/plan_and_then_execute_agent/shared/chat/graph/base_chat_graph.py` 구현을 기준으로 현재 동작을 정리한다.

Builder 주입형 그래프 실행기입니다.
그래프 입력 생성, `thread_id` 구성, 이벤트 정규화(custom/updates)와 스트림 노드 필터링을 공통 처리합니다.

## 주요 구성

1. `DefaultChatGraphInput`: 기본 그래프 입력 모델
2. `BaseChatGraph.compile()`: builder 컴파일 및 실행 객체 보관
3. `invoke()/ainvoke()`: 최종 `assistant_message` 반환
4. `stream_events()/astream_events()`: 표준 이벤트 반복자 반환
5. `set_stream_node()`: 노드별 허용 이벤트 정책 교체

## 실패 경로

- `CHAT_STREAM_EMPTY`: invoke/ainvoke 결과가 비어 있을 때
- `CHAT_STREAM_NODE_INVALID`: `stream_node` 설정 형식이 잘못됐을 때

## 관련 문서

- `docs/shared/chat/interface/ports.md`
- `docs/shared/chat/services/chat_service.md`
