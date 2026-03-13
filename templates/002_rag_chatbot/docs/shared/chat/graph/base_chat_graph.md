# DefaultChatGraphInput 가이드

이 문서는 `src/rag_chatbot/shared/chat/graph/base_chat_graph.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

LangGraph builder를 공통 실행기로 감싸고, 외부로 노출할 이벤트만 필터링하는 그래프 실행 어댑터다.

## 2. 공개 구성

- 클래스 `DefaultChatGraphInput`
  공개 메서드: 없음
- 클래스 `BaseChatGraph`
  공개 메서드: `set_stream_node`, `compile`, `invoke`, `ainvoke`, `stream_events`, `astream_events`

## 3. 코드 설명

- `stream_mode=["custom", "updates"]`를 사용해 LangGraph 이벤트를 공통 형식으로 변환한다.
- `stream_node` 설정에 포함된 노드/이벤트만 외부로 노출한다.
- `thread_id`는 `session_id`를 기본값으로 사용한다.

## 4. 유지보수/추가개발 포인트

- 새 노드 이벤트를 외부에 노출하려면 core 그래프의 `stream_node`와 이 어댑터의 허용 정책을 같이 업데이트해야 한다.
- 입력 모델에 필드를 추가할 때는 core state 타입과 라우터 요청 모델까지 연쇄 영향을 점검해야 한다.

## 5. 관련 문서

- `docs/shared/overview.md`
- `docs/shared/chat/README.md`
