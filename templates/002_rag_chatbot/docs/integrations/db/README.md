# Integrations DB

## 계층

- `base`: 엔진 포트, 공용 모델, 세션/풀 포트, query builder 포트
- `client.py`: 상위 계층 퍼사드
- `query_builder`: 읽기/쓰기/삭제 DSL
- `engines/sqlite`: 기본 Chat 저장소 경로
- `engines/lancedb`: 기본 online retrieval 경로
- `engines/postgres`: 관계형 저장 + pgvector
- `engines/mongodb`: 문서형 저장
- `engines/redis`: keyspace 기반 저장과 벡터 유틸
- `engines/elasticsearch`: 인덱스 기반 검색

## 현재 활성 사용 경로

- Chat 이력 기본 저장소: SQLite
- online retrieval: LanceDB
- ingestion backend 선택: LanceDB, PostgreSQL, Elasticsearch

## 조립 필요 경로

- PostgreSQL, MongoDB, Redis는 엔진 구현과 테스트는 있지만 기본 Chat 런타임에 자동 조립되지는 않는다.
