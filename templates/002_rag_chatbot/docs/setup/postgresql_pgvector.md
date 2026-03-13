# PostgreSQL + pgvector

## 현재 범위

- ingestion backend로 지원된다.
- 기본 Chat 저장소로는 조립돼 있지 않다.
- online retrieval 기본 경로도 아니다.

## 관련 코드

- 엔진: `src/rag_chatbot/integrations/db/engines/postgres/*`
- 적재: `ingestion/steps/upsert_postgres_step.py`
- 벡터 처리: `vector_store.py`, `vector_adapter.py`
- 런타임 전환 지점: `src/rag_chatbot/api/chat/services/runtime.py`

## 환경 변수

- `POSTGRES_DSN`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_USER`
- `POSTGRES_PW`
- `POSTGRES_DATABASE`

## 주의

- pgvector 차원과 `GEMINI_EMBEDDING_DIM`이 맞아야 한다.
- Chat 저장소까지 옮기려면 repository 질의, 정렬, `request_id` 멱등 저장 경로를 함께 확인해야 한다.
