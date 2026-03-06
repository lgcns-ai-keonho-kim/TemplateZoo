# Base Chat Graph

이 문서는 `src/rag_chatbot/shared/chat/graph/base_chat_graph.py`의 공통 그래프 실행 구현을 설명한다.

## 1. 목적

- Builder 주입형 그래프 실행 공통 로직을 제공한다.
- 그래프 이벤트(`custom`, `updates`)를 표준 이벤트 구조로 정규화한다.
- 스트림 노드 정책 기반 필터링을 수행한다.

## 2. 핵심 구성

| 구성 | 설명 |
| --- | --- |
| `DefaultChatGraphInput` | 기본 그래프 입력 모델 (`session_id`, `user_message`, `history`, `assistant_message`) |
| `BaseChatGraph` | 컴파일/실행/스트림 이벤트 변환 구현체 |

초기화 인자:

1. `builder`: 실제 그래프 컴파일 객체
2. `checkpointer`: 그래프 상태 저장소(선택)
3. `stream_node`: 노드별 허용 이벤트 정책
4. `input_model`: 입력 모델 커스터마이징 타입

## 3. 실행 메서드

1. `compile`: 그래프를 컴파일하고 내부에 캐시한다.
2. `invoke`, `ainvoke`: 최종 `assistant_message`를 추출해 문자열로 반환한다.
3. `stream_events`, `astream_events`: 그래프 이벤트를 순회하며 허용 이벤트만 반환한다.

오류 규칙:

- `assistant_message`가 비어 있으면 `CHAT_STREAM_EMPTY` 예외를 발생시킨다.

## 4. 이벤트 정규화

`_to_events` 변환 규칙:

1. `mode="custom"`: `{node, event, data}` 형태를 그대로 이벤트로 변환
2. `mode="updates"`: 노드 델타를 순회하며 이벤트 목록으로 변환
3. 지원하지 않는 mode 또는 비정상 payload는 무시

## 5. 스트림 필터 정책

- `set_stream_node`로 정책을 교체한다.
- 내부 정규화 결과(`node -> set(event)`)로 필터링한다.
- 허용되지 않은 이벤트는 상위로 전달하지 않는다.

## 6. 관련 문서

- `docs/shared/chat/interface/ports.md`
- `docs/shared/chat/services/chat_service.md`
- `docs/core/chat.md`
