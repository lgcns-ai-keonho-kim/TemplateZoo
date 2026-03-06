# `services/chat_service.py` 레퍼런스

## 1. 모듈 목적

`ChatService`는 저장소/메모리/그래프 실행을 결합하는 서비스 레이어다.

## 2. 핵심 클래스

1. `ChatService`
- 세션 CRUD: `create_session`, `list_sessions`, `get_session`, `delete_session`
- 메시지 실행: `invoke`, `ainvoke`, `stream`, `astream`
- 멱등 저장: `persist_assistant_message`
- 보조: `append_assistant_message`

## 3. 입력/출력

1. 실행 경로
- 사용자 입력 저장 -> 최근 문맥 구성 -> 그래프 실행 -> assistant 저장

2. 문맥 구성
- `ChatSessionMemoryStore.lrange`로 최근 메시지 조회
- `context_window` 기준으로 슬라이싱

3. 스트림 완료 처리
- `token` 누적 우선
- `assistant_message` fallback 보조
- 최종 빈 응답이면 예외

4. 멱등 저장
- `is_request_committed(request_id)` 선검사
- 미커밋 시에만 `append_assistant_message` + `mark_request_committed`

## 4. 실패 경로

1. `CHAT_SESSION_NOT_FOUND`
- 조건: 세션 조회/삭제/메시지 추가 시 세션 없음

2. `CHAT_STREAM_EMPTY`
- 조건: invoke/ainvoke/stream/astream 최종 응답 공백

3. `CHAT_MESSAGE_EMPTY`
- 조건: 사용자/assistant 메시지가 공백

## 5. 연계 모듈

1. 그래프: `graph/base_chat_graph.py` 또는 core graph 구현체
2. 저장소: `repositories/history_repository.py`
3. 메모리: `memory/session_store.py`

## 6. 운영 포인트

1. `CHAT_MEMORY_MAX_MESSAGES`가 문맥 비용/응답 품질에 직접 영향
2. 멱등 저장 실패 시 중복 응답 또는 저장 누락 이슈가 발생할 수 있음
3. 세션 삭제 시 메모리(`clear_session`) 정리가 함께 수행되는지 확인

## 7. 변경 시 영향 범위

1. 스트림 이벤트 해석 변경 시 `ServiceExecutor._normalize_graph_event` 동시 수정 필요
2. `persist_assistant_message` 변경 시 request commit 스키마와 함께 검증 필요
