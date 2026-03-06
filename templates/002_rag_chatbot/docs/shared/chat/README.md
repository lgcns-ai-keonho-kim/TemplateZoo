# Shared Chat 문서 개요

이 문서는 `src/rag_chatbot/shared/chat` 패키지의 모듈 구조와 책임을 코드 기준으로 정리한다.

## 1. 디렉터리 구조

```text
src/rag_chatbot/shared/chat/
  interface/
    ports.py
  graph/
    base_chat_graph.py
  memory/
    session_store.py
  nodes/
    _state_adapter.py
    branch_node.py
    fanout_branch_node.py
    function_node.py
    llm_node.py
    message_node.py
  repositories/
    history_repository.py
    schemas/
      session_schema.py
      message_schema.py
      request_commit_schema.py
  services/
    chat_service.py
    service_executor.py
```

## 2. 실행 흐름 요약

1. `ServiceExecutor`가 작업 큐에 채팅 요청을 적재하고 워커에서 소비한다.
2. `ChatService`가 세션/메시지 저장과 그래프 실행을 조합한다.
3. `BaseChatGraph`가 그래프 이벤트를 표준 이벤트로 변환한다.
4. `ServiceExecutor`가 이벤트를 `start/token/references/done/error` 형식으로 버퍼에 적재한다.
5. 라우터가 SSE로 이벤트를 전달하고, done 이벤트 기준으로 assistant 저장 후처리를 수행한다.

## 3. 모듈 문서 인덱스

| 영역 | 문서 |
| --- | --- |
| 인터페이스 | `docs/shared/chat/interface/ports.md` |
| 그래프 실행 | `docs/shared/chat/graph/base_chat_graph.md` |
| 세션 메모리 | `docs/shared/chat/memory/session_store.md` |
| 공통 노드 | `docs/shared/chat/nodes/*.md` |
| 이력 저장소 | `docs/shared/chat/repositories/history_repository.md` |
| 저장소 스키마 | `docs/shared/chat/repositories/schemas/*.md` |
| 실행 서비스 | `docs/shared/chat/services/chat_service.md` |
| 실행 오케스트레이터 | `docs/shared/chat/services/service_executor.md` |

## 4. 우선 읽기 순서

1. `docs/shared/chat/services/service_executor.md`
2. `docs/shared/chat/services/chat_service.md`
3. `docs/shared/chat/repositories/history_repository.md`
4. `docs/shared/chat/graph/base_chat_graph.md`
5. `docs/shared/chat/interface/ports.md`
6. `docs/shared/chat/memory/session_store.md`
7. `docs/shared/chat/nodes/llm_node.md`

## 5. 관련 문서

- `docs/shared/overview.md`
- `docs/api/chat.md`
- `docs/core/chat.md`
