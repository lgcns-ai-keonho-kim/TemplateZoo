# Core 모듈 가이드

이 문서는 `src/rag_chatbot/core`가 채팅 정책을 어떻게 정의하는지와, 어디까지가 core 책임인지 정리한다.

## 1. 책임 경계

- `core`는 세션/메시지 같은 도메인 모델, 그래프 상태, 프롬프트, 노드, 그래프 연결 규칙을 담당한다.
- `core`는 FastAPI, HTTP DTO, 큐/버퍼 백엔드, DB 드라이버 세부 구현을 직접 다루지 않는다.
- 외부 기술 의존은 `integrations`와 `shared`를 통해 연결된다.

## 2. 현재 구조

- `models`: `ChatSession`, `ChatMessage`, `TurnResult`
- `const`: DB 경로, 기본 page size, context window, safeguard 메시지
- `state`: `ChatGraphState`
- `prompts`: `chat_prompt.py`, `safeguard_prompt.py`, `context_strategy_prompt.py`, `keyword_generation.py`, `relevance_filter.py`, `fallback_query_generation.py`
- `nodes`: safeguard, context strategy, 다단 RAG, response 조립 노드
- `graphs`: `chat_graph.py`
- `utils`: 도메인-문서 매퍼

## 3. 읽기 순서

1. `docs/core/chat.md`
2. `src/rag_chatbot/core/chat/state/graph_state.py`
3. `src/rag_chatbot/core/chat/nodes/__init__.py`
4. `src/rag_chatbot/core/chat/prompts/*.py`
5. `src/rag_chatbot/core/chat/graphs/chat_graph.py`

## 4. 유지보수/추가개발 포인트

- 프롬프트 파일이 존재한다고 모두 활성 경로는 아니므로, 실제 그래프에서 참조되는 프롬프트와 확장용 프롬프트를 구분해서 봐야 한다.
- 새 노드를 추가할 때는 state 키, prompt 입력 변수, stream 노출 정책을 한 번에 설계하는 편이 안전하다.
- core는 현재 온라인 검색 노드에서 LanceDB 경로를 직접 사용하므로, 검색 백엔드 추상화를 도입할 때는 core와 integrations 경계를 다시 정리해야 한다.

## 5. 관련 문서

- `docs/core/chat.md`
- `docs/shared/chat/README.md`
- `docs/integrations/overview.md`
