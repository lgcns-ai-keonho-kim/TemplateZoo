# 설정 개요

## 최소 로컬 실행

1. 루트 `.env` 생성
2. `GEMINI_MODEL`, `GEMINI_EMBEDDING_MODEL`, `GEMINI_PROJECT`, `LANCEDB_URI`, `CHAT_DB_PATH` 설정
3. `uv run python ingestion/ingest.py --backend lancedb --input-root data/ingestion-doc`
4. `uv run uvicorn rag_chatbot.api.main:app --host 0.0.0.0 --port 8000 --reload`
5. `/health`, `/docs`, `/ui` 확인

## 순서

1. `docs/setup/env.md`
2. `docs/setup/ingestion.md`
3. `docs/setup/lancedb.md`
4. `docs/setup/postgresql_pgvector.md`
5. `docs/setup/mongodb.md`
6. `docs/setup/filesystem.md`

## 기본 경로

- 기본 Chat 저장소: SQLite
- 기본 벡터 저장소: LanceDB
- 기본 Chat 런타임 큐/버퍼: InMemory
