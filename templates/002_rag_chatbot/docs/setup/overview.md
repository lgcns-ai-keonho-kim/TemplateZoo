# Setup 가이드 개요

이 문서는 로컬 실행부터 backend 전환까지 어떤 setup 문서를 어떤 순서로 읽어야 하는지 정리한다.

## 1. 권장 읽기 순서

1. `docs/setup/env.md`
2. `docs/setup/ingestion.md`
3. `docs/setup/lancedb.md`
4. `docs/setup/postgresql_pgvector.md`
5. `docs/setup/mongodb.md`
6. `docs/setup/filesystem.md`

## 2. 최소 로컬 실행 경로

1. 루트 `.env`를 만든다.
2. `GEMINI_MODEL`, `GEMINI_EMBEDDING_MODEL`, `GEMINI_PROJECT`, `LANCEDB_URI`, `CHAT_DB_PATH`를 설정한다.
3. `uv run python ingestion/ingest.py --backend lancedb --input-root data/ingestion-doc`를 실행한다.
4. `uv run uvicorn rag_chatbot.api.main:app --host 0.0.0.0 --port 8000 --reload`로 서버를 띄운다.
5. `/health`, `/docs`, `/ui`를 순서대로 확인한다.

## 3. 유지보수/추가개발 포인트

- setup 문서는 실제 코드 기본값과 예시값을 구분해 적는 편이 운영 혼선을 줄인다.
- backend 전환은 엔진 구현만이 아니라 runtime 조립, ingestion CLI, 환경 변수까지 함께 확인해야 한다.

## 4. 관련 문서

- `docs/setup/env.md`
- `docs/setup/ingestion.md`
- `docs/integrations/overview.md`
