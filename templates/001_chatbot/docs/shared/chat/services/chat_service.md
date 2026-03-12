# `services/chat_service.py` 레퍼런스

`ChatService`는 저장소, 세션 메모리, 그래프 실행기를 묶는 서비스 계층이다. 현재 채팅 도메인에서 동기/비동기 실행과 세션 CRUD를 모두 담당한다.

## 1. 코드 설명

핵심 동작:

1. 세션 생성과 조회
2. 사용자 메시지 저장
3. 최근 문맥 히스토리 구성
4. 그래프 실행
5. assistant 메시지 저장
6. `request_id` 기반 멱등 저장

실행 순서:

```text
세션 확인
 -> 사용자 메시지 append
 -> 메모리 캐시 보장
 -> context_window 만큼 히스토리 구성
 -> graph invoke/stream
 -> assistant 메시지 append 또는 멱등 저장
```

주요 오류 코드:

1. `CHAT_SESSION_NOT_FOUND`
2. `CHAT_STREAM_EMPTY`
3. `CHAT_MESSAGE_EMPTY`

## 2. 유지보수 포인트

1. `_normalize_message()`는 공백 메시지를 허용하지 않는다. 입력 검증 정책을 바꾸면 저장소 예외와 사용자 경험이 동시에 바뀐다.
2. `_build_context_history()`는 메모리 캐시 기준으로 동작한다. 저장소에서 직접 히스토리를 재구성하도록 바꾸면 성능과 최신성의 균형이 달라진다.
3. `stream()`과 `astream()`은 `token` 우선, `assistant_message` fallback 구조다. blocked 경로를 유지하려면 이 해석을 건드릴 때 주의해야 한다.

## 3. 추가 개발/확장 가이드

1. 새 그래프를 붙이더라도 `GraphPort` 계약만 맞으면 `ChatService`는 대부분 재사용 가능하다.
2. 세션 제목 자동 생성 같은 정책을 추가하려면 저장소가 아니라 서비스 계층에서 유스케이스 단위로 넣는 편이 구조상 맞다.

## 4. 관련 코드

- `src/chatbot/shared/chat/memory/session_store.py`
- `src/chatbot/shared/chat/repositories/history_repository.py`
- `src/chatbot/shared/chat/graph/base_chat_graph.py`
