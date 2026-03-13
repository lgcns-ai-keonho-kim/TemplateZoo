# ServiceExecutor 가이드

이 문서는 `src/rag_chatbot/shared/chat/services/service_executor.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

작업 큐 소비, 이벤트 버퍼 적재, SSE 정규화, done 후 저장 후처리를 담당하는 실행 오케스트레이터다.

## 2. 공개 구성

- 클래스 `ServiceExecutor`
  공개 메서드: `submit_job`, `get_session_status`, `stream_events`, `shutdown`

## 3. 코드 설명

- 현재 런타임은 `InMemoryQueue`, `InMemoryEventBuffer`를 기본으로 조립한다.
- 공개 이벤트 타입은 `start`, `token`, `references`, `done`, `error`다.
- 동일 세션은 내부 락으로 직렬화해 저장/스트림 순서를 지킨다.

## 4. 유지보수/추가개발 포인트

- 새 이벤트 타입을 추가하면 SSE payload 모델, 프런트 파서, 테스트까지 한 번에 수정해야 한다.
- 큐/버퍼 백엔드를 바꾸려면 `api/chat/services/runtime.py` 조립과 timeout 설정을 같이 점검해야 한다.

## 5. 관련 문서

- `docs/shared/overview.md`
- `docs/shared/chat/README.md`
