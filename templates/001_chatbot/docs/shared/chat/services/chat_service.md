# `services/chat_service.py` 레퍼런스

`ChatService`는 저장소, 세션 메모리, 그래프 실행기를 묶는 서비스 계층이다.

## 1. 핵심 동작

1. 세션 생성과 조회
2. 사용자 메시지 저장
3. 최근 문맥 히스토리 구성
4. 그래프 실행
5. assistant 메시지 저장
6. `request_id` 기반 멱등 저장

실행 흐름:

```text
세션 확인
 -> 사용자 메시지 append
 -> 세션 메모리 보장
 -> context_window 기준 최근 히스토리 구성
 -> graph invoke/stream
 -> assistant 메시지 append 또는 멱등 저장
```

## 2. 현재 구현 특징

1. 메모리 한도는 `CHAT_MEMORY_MAX_MESSAGES` 환경 변수로 정한다.
2. `stream()`과 `astream()`은 `token`을 우선 누적하고, 필요하면 `assistant_message`를 fallback으로 사용한다.
3. 최종 본문이 비면 `CHAT_STREAM_EMPTY` 예외를 낸다.

## 3. 주요 오류 코드

1. `CHAT_SESSION_NOT_FOUND`
2. `CHAT_STREAM_EMPTY`
3. `CHAT_MESSAGE_EMPTY`

## 4. 유지보수 포인트

1. `_build_context_history()`는 저장소가 아니라 세션 메모리 기준으로 최근 문맥을 만든다.
2. `persist_assistant_message()`는 저장 후 `mark_request_committed()`를 호출해 멱등성을 보장한다.
3. 세션 삭제 시 메모리 캐시도 함께 비운다.

## 5. 관련 문서

- `docs/core/chat.md`
- `docs/shared/chat/services/service_executor.md`
- `docs/shared/chat/repositories/history_repository.md`
