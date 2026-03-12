# `graph/base_chat_graph.py` 레퍼런스

`BaseChatGraph`는 LangGraph builder를 직접 노출하지 않고, 공통 실행 인터페이스로 감싸는 구현체다.

## 1. 코드 설명

핵심 구성:

1. `DefaultChatGraphInput`
2. `BaseChatGraph`

주요 책임:

1. 입력 모델 검증
2. 그래프 컴파일과 캐싱
3. 동기/비동기 실행
4. `custom`, `updates` 스트림 이벤트를 공통 이벤트 형식으로 변환
5. `stream_node` 정책에 맞는 이벤트만 외부로 노출

이벤트 표준 형식:

```json
{
  "node": "response",
  "event": "token",
  "data": "안"
}
```

## 2. 실제 동작 포인트

1. `compile()`은 builder를 컴파일해 내부 `_compiled_graph`에 보관한다.
2. `invoke()`와 `ainvoke()`는 최종 결과에서 `assistant_message`만 추출한다.
3. `stream_events()`와 `astream_events()`는 `stream_mode=["custom", "updates"]`를 사용한다.
4. `configurable.thread_id`가 비어 있으면 `session_id`로 자동 보정한다.

실패 조건:

1. `assistant_message`가 비어 있으면 `CHAT_STREAM_EMPTY`
2. `stream_node` 설정값이 문자열/시퀀스가 아니면 `CHAT_STREAM_NODE_INVALID`

## 3. 유지보수 포인트

1. 이 클래스는 `assistant_message`를 최종 출력 키로 가정한다. 출력 키를 바꾸는 그래프를 도입하면 `_extract_assistant_message()` 또는 입력 모델을 함께 조정해야 한다.
2. 이벤트 스키마는 `ServiceExecutor._normalize_graph_event()`와 쌍으로 맞아야 한다.
3. `stream_node`에 없는 이벤트는 무조건 버려지므로, 디버그 목적 이벤트를 추가해도 바로 외부에 노출되지는 않는다.

## 4. 추가 개발/확장 가이드

1. 새 그래프를 추가할 때는 `input_model`만 교체해도 공통 실행기를 재사용할 수 있다.
2. 노드별 이벤트 공개 범위를 세밀하게 나누려면 `stream_node`만 조정하고 상위 계층을 건드리지 않는 방향이 안전하다.

## 5. 관련 코드

- `src/chatbot/core/chat/graphs/chat_graph.py`
- `src/chatbot/shared/chat/interface/ports.py`
- `src/chatbot/shared/chat/services/chat_service.py`
