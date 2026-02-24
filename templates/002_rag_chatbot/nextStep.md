# Next Step - SQLite RDB 전용화 / LanceDB 벡터 전환

## 완료된 결정 사항
1. SQLite는 RDB 전용이며 벡터 검색을 지원하지 않는다.
2. 파일 기반 벡터 저장소는 LanceDB를 사용한다.
3. 기존 `sqlite-vec` 기반 ingestion 경로는 `ingest_lancedb.py`로 대체했다.
4. RAG 검색 노드는 `LANCEDB_URI`를 사용해 LanceDB를 조회한다.

## 구현 체크리스트
1. SQLite 엔진
- [x] `SQLiteEngine(enable_vector=...)` 인자 제거
- [x] 벡터 검색 API 명시 오류 처리
- [x] 벡터 스키마/컬럼 생성 차단
- [x] `sqlite/vector_store.py`, `sqlite/vector_codec.py` 제거

2. LanceDB 엔진
- [x] `LanceDBEngine` 추가
- [x] CRUD + vector_search 구현
- [x] 엔진 export 연결(`engines/__init__.py`, `db/__init__.py`)

3. ingestion/RAG 전환
- [x] `ingestion/ingest_lancedb.py` 추가
- [x] `ingestion/steps/upsert_lancedb_step.py` 추가
- [x] `ingestion/core/db.py`의 LanceDB 팩토리/스키마 추가
- [x] `ingestion/core/documents.py`의 LanceDB 문서 변환 추가
- [x] `rag_retrieve_node`를 LanceDB 기반으로 전환

4. 테스트/문서
- [x] SQLite 벡터 테스트를 비지원 검증으로 변경
- [x] LanceDB 벡터 테스트 추가
- [x] RAG 스모크 테스트를 LanceDB 기준으로 교체
- [x] `docs/setup/lancedb.md` 추가 및 sqlite-vec 문서 제거
- [x] ENV/README 문서에 `LANCEDB_URI` 반영

## 사용자 실행 검증 커맨드
1. 타입 체크
`uv run ty check src`

2. SQLite CRUD + 벡터 비지원
`uv run pytest tests/integrations/db/CRUD/test_sqlite_engine_crud.py -v`
`uv run pytest tests/integrations/db/Vector/test_sqlite_engine_vector.py -v`

3. LanceDB 벡터 검색
`uv run pytest tests/integrations/db/Vector/test_lancedb_engine_vector.py -v`

4. RAG 스모크 (실환경 키 필요)
`uv run pytest tests/core/chat/nodes/test_rag_pipeline_lancedb_smoke.py -v`
