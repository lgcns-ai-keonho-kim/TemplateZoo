# PostgreSQL + pgvector 설정 가이드

이 문서는 PostgreSQL 엔진과 pgvector 연동이 현재 코드에서 어디까지 준비돼 있는지 설명한다.

## 1. 현재 사용 범위

- ingestion backend로는 지원된다.
- Chat 이력 기본 저장소로는 조립돼 있지 않다.
- Chat 저장소나 runtime을 PostgreSQL로 바꾸려면 `api/chat/services/runtime.py`를 직접 수정해야 한다.

## 2. 현재 코드 구성

- 엔진 구현: `src/rag_chatbot/integrations/db/engines/postgres/*`
- 적재 경로: `ingestion/steps/upsert_postgres_step.py`
- 벡터 인덱스 관리: `vector_store.py`, `vector_adapter.py`

## 3. 유지보수/추가개발 포인트

- pgvector 차원과 `GEMINI_EMBEDDING_DIM`이 맞지 않으면 적재와 검색이 모두 깨진다.
- Chat 저장소까지 옮길 계획이라면 repository query, list 정렬, request_id 멱등 저장 정책을 먼저 검증해야 한다.
- 운영 DB로 쓸 때는 연결 풀, 마이그레이션, 인덱스 준비 절차를 별도 운영 문서로 분리하는 편이 좋다.

## 4. 관련 문서

- `docs/setup/env.md`
- `docs/setup/ingestion.md`
- `docs/integrations/db/engines/postgres/engine.md`
