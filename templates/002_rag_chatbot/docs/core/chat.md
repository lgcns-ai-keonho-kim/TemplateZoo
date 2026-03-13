# Core Chat

## 그래프 순서

- 진입점: `safeguard`
- 차단 경로: `safeguard -> safeguard_route -> blocked -> END`
- 일반 경로: `safeguard -> safeguard_route -> context_strategy_prepare -> context_strategy -> context_strategy_route -> context_strategy_finalize -> response`
- RAG 경로: `context_strategy_finalize -> rag_keyword_llm -> rag_keyword_postprocess -> rag_retrieve -> rag_chunk_dedup -> rag_relevance_prepare -> rag_relevance_judge/rag_relevance_collect -> rag_file_page_dedup -> rag_final_topk -> rag_format -> response`

## 핵심 규칙

- `safeguard_node`는 `PASS`, `PII`, `HARMFUL`, `PROMPT_INJECTION` 중 하나를 반환한다.
- `safeguard_route_node`는 `PROMPT_INJETION` 오타 alias를 교정하고, 알 수 없는 값은 `HARMFUL`로 강등한다.
- `context_strategy_route_node`는 전략 값을 `REUSE_LAST_ASSISTANT`, `USE_RAG`로 정규화한다.
- `context_strategy_finalize_node`는 최근 assistant 메시지가 없으면 `REUSE_LAST_ASSISTANT`를 `USE_RAG`로 바꾼다.
- `rag_retrieve_node`는 현재 LanceDB `rag_chunks` 컬렉션을 직접 사용한다.
- `rag_format_node`는 `rag_context`와 `rag_references`를 만들고, 파일 단위로 reference를 묶어 `page_nums`를 합친다.

## 상태 키

- 입력: `session_id`, `user_message`, `history`
- safeguard: `safeguard_result`, `safeguard_route`, `safeguard_reason`
- context strategy: `context_strategy`, `context_strategy_raw`, `last_assistant_message`
- retrieval: `rag_keyword_raw`, `rag_queries`, `rag_retrieved_chunks`, `rag_candidates`
- relevance: `rag_relevance_batch_id`, `rag_relevance_judge_inputs`, `rag_relevance_candidate_index`, `rag_relevance_candidate`, `rag_relevance_judge_results`, `rag_relevance_passed_docs`, `rag_relevance_raw`
- post filter: `rag_file_page_deduped_docs`, `rag_filtered_docs`
- 최종 출력: `rag_context`, `rag_references`, `assistant_message`

## stream 노출

- `safeguard`: `safeguard_result`
- `safeguard_route`: `safeguard_route`, `safeguard_result`
- `rag_format`: `rag_context`, `rag_references`
- `response`: `token`, `assistant_message`
- `blocked`: `assistant_message`
