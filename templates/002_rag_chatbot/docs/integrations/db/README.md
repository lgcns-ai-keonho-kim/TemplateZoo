# Integrations DB 가이드

이 문서는 DB 계층 전체 구조와, 어떤 엔진이 어떤 역할을 하는지 현재 코드 기준으로 설명한다.

## 1. 현재 계층 구조

- `base`: 엔진 포트, 공용 모델, query builder 포트, 세션/풀 포트
- `client.py`: 상위 계층이 직접 사용하는 퍼사드
- `query_builder`: 읽기/쓰기/삭제 DSL
- `engines/sqlite`: 기본 Chat 저장소
- `engines/lancedb`: 현재 RAG 벡터 검색 기본 경로
- `engines/postgres`: 관계형 저장 + pgvector
- `engines/mongodb`: 문서형 저장
- `engines/redis`: keyspace 기반 저장과 벡터 유틸
- `engines/elasticsearch`: 인덱스 기반 검색

## 2. 현재 활성 사용 경로

- Chat 이력 기본 저장소: SQLite (`ChatHistoryRepository` 기본 생성 경로)
- online retrieval: LanceDB (`rag_retrieve_node`)
- ingestion 백엔드 선택: LanceDB, PostgreSQL, Elasticsearch

## 3. 유지보수/추가개발 포인트

- 새 엔진 기능을 추가하면 `BaseDBEngine`, `DBClient`, 관련 query builder, 문서까지 함께 수정해야 한다.
- 스키마나 필터 표현을 바꾸면 mapper, condition/filter builder, 테스트가 동시에 영향을 받는다.
- "구현이 있다"와 "현재 조립돼 있다"를 문서에서 구분해야 운영 혼선을 줄일 수 있다.

## 4. 관련 문서

- `docs/integrations/overview.md`
- `docs/setup/lancedb.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/setup/mongodb.md`
