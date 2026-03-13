# Core Chat 가이드

이 문서는 `src/rag_chatbot/core/chat`의 그래프 구조, 상태 키, 프롬프트 정책, 유지보수 포인트를 현재 코드 기준으로 설명한다.

## 1. 그래프 실행 순서

- 진입점: `safeguard`
- 차단 경로: `safeguard -> safeguard_route -> blocked -> END`
- 일반 경로: `safeguard -> safeguard_route -> context_strategy_prepare -> context_strategy -> context_strategy_route -> context_strategy_finalize -> response`
- RAG 경로: `context_strategy_finalize -> rag_keyword_llm -> rag_keyword_postprocess -> rag_retrieve -> rag_chunk_dedup -> rag_relevance_prepare -> rag_relevance_judge/rag_relevance_collect -> rag_file_page_dedup -> rag_final_topk -> rag_format -> response`

## 2. 현재 핵심 규칙

- `safeguard_node`는 `PASS`, `PII`, `HARMFUL`, `PROMPT_INJECTION` 중 하나를 반환한다.
- `safeguard_route_node`는 `PROMPT_INJETION` 오타를 alias로 교정하고, 알 수 없는 토큰은 `HARMFUL`로 강등한다.
- `context_strategy_route_node`는 전략 토큰을 `REUSE_LAST_ASSISTANT`, `USE_RAG`로 정규화한다.
- `context_strategy_finalize_node`는 최근 assistant 메시지가 없으면 `REUSE_LAST_ASSISTANT`를 강제로 `USE_RAG`로 바꾼다.
- `rag_retrieve_node`는 현재 코드상 LanceDB `rag_chunks` 컬렉션을 직접 사용한다.
- `rag_format_node`는 최종 `rag_context`와 `rag_references`를 만들고, reference를 파일 단위로 묶어 `page_nums`를 병합한다.

## 3. 상태 키 묶음

- 입력: `session_id`, `user_message`, `history`
- safeguard: `safeguard_result`, `safeguard_route`, `safeguard_reason`
- context strategy: `context_strategy`, `context_strategy_raw`, `last_assistant_message`
- retrieval: `rag_keyword_raw`, `rag_queries`, `rag_retrieved_chunks`, `rag_candidates`
- relevance: `rag_relevance_batch_id`, `rag_relevance_judge_inputs`, `rag_relevance_candidate_index`, `rag_relevance_candidate`, `rag_relevance_judge_results`, `rag_relevance_passed_docs`, `rag_relevance_raw`
- post filter: `rag_file_page_deduped_docs`, `rag_filtered_docs`
- 최종 출력: `rag_context`, `rag_references`, `assistant_message`

## 4. stream 노출 정책

- `safeguard`: `safeguard_result`
- `safeguard_route`: `safeguard_route`, `safeguard_result`
- `rag_format`: `rag_context`, `rag_references`
- `response`: `token`, `assistant_message`
- `blocked`: `assistant_message`

## 5. 프롬프트 유지 포인트

- 활성 사용 프롬프트는 `CHAT_PROMPT`, `SAFEGUARD_PROMPT`, `CONTEXT_STRATEGY_PROMPT`, `KEYWORD_GENERATION_PROMPT`, `RELEVANCE_FILTER_PROMPT`다.
- `fallback_query_generation.py`는 현재 그래프 실행 경로에는 연결되지 않는다.
- `CHAT_PROMPT`는 RAG 컨텍스트 기반 응답을 강하게 요구하고, 정보 부족을 숨기지 않도록 설계돼 있다.

## 6. 유지보수/추가개발 포인트

- fan-out/fan-in을 바꾸면 `rag_relevance_prepare`, `rag_relevance_judge`, `rag_relevance_collect`, `ChatGraphState` 병합 규칙을 함께 봐야 한다.
- 새 노드 이벤트를 외부에 노출하려면 `chat_graph.stream_node`, `BaseChatGraph`, `ServiceExecutor`, 프런트 SSE 파서를 한 번에 수정해야 한다.
- 검색 백엔드를 교체할 계획이 있다면 현재 core가 LanceDB 경로에 직접 결합되어 있다는 점부터 먼저 해소해야 한다.

## 7. 관련 문서

- `docs/core/overview.md`
- `docs/api/chat.md`
- `docs/shared/chat/README.md`
- `docs/setup/ingestion.md`
