# DB 통합 아키텍처 명세

이 문서는 `src/base_template/integrations/db` 계층의 공통 계약과 엔진별 구현 책임을 정의한다.

## 계층 구성

| 계층 | 파일 | 역할 |
| --- | --- | --- |
| 공통 모델 | `integrations/db/base/models.py` | 스키마, 문서, 필터, 정렬, 벡터 검색 DTO |
| 엔진 인터페이스 | `integrations/db/base/engine.py` | CRUD + 벡터 검색 추상 계약 |
| 파사드 | `integrations/db/client.py` | 스키마 등록/검증, 엔진 호출 단순화 |
| Query Builder | `integrations/db/query_builder/*` | 읽기/쓰기/삭제 DSL |
| 엔진 구현 | `integrations/db/engines/*` | DB별 실제 CRUD/검색/벡터 처리 |

## 핵심 데이터 계약

### `CollectionSchema`

- `name`, `primary_key`는 필수 식별자이다.
- `payload_field`가 있으면 payload JSON 저장을 허용한다.
- `vector_field`가 있으면 벡터 저장/검색이 가능하다.
- `validate_document`, `validate_query`가 스키마 위반을 사전 차단한다.

### `Document`

- `doc_id`: 문서 식별자
- `fields`: 컬럼 기반 데이터
- `payload`: JSON 데이터
- `vector`: 벡터 데이터

### `Query`

- `filter_expression`, `sort`, `pagination`을 조합한다.
- `FieldSource`로 컬럼/페이로드 필드 출처를 지정한다.

### `VectorSearchRequest`

- `collection`, `vector`, `top_k`, `filter_expression`, `include_vectors`

## `DBClient` 책임

1. 엔진 연결/종료 관리
2. 스키마 등록 및 조회
3. 스키마 기반 문서/쿼리 검증
4. 엔진별 동작 차이 캡슐화
5. DSL 빌더 제공 (`read`, `write`, `delete`)

## 엔진별 구현 책임

| 엔진 | 파일 | 벡터 검색 | 특징 |
| --- | --- | --- | --- |
| SQLite | `engines/sqlite/engine.py` | 지원(옵션) | `sqlite-vec` 확장 사용, 로컬 파일 DB |
| Redis | `engines/redis/engine.py` | 지원(옵션) | 해시 저장 + 전체 스캔 기반 cosine 유사도 |
| PostgreSQL | `engines/postgres/engine.py` | 지원 | PGVector 기반 유사도 검색 |
| Elasticsearch | `engines/elasticsearch/engine.py` | 지원 | `knn` 검색 사용, `drop_column` 미지원 |
| MongoDB | `engines/mongodb/engine.py` | 미지원 | CRUD 중심 구현, 벡터 검색 비활성 |

## 의존성 방향

```text
core/repositories/*
  -> integrations/db/client.DBClient
     -> integrations/db/base (models, engine)
     -> integrations/db/engines/*
```

`core`와 `api`는 DB 엔진 구체 클래스를 직접 호출하지 않는다. 엔진 교체 지점은 `DBClient` 생성부다.

## 동작 규칙

1. 컬렉션 생성 전에 스키마를 등록한다.
2. 문서 저장 전에 스키마 검증을 통과한다.
3. 벡터 검색은 `schema.vector_field`와 `engine.supports_vector_search` 두 조건이 모두 필요하다.
4. 엔진별 제약은 예외로 즉시 드러난다.

## 제약 사항

1. Redis 벡터 검색은 필터를 지원하지 않는다.
2. MongoDB 엔진은 벡터 검색을 제공하지 않는다.
3. Elasticsearch는 컬럼 삭제를 직접 지원하지 않는다.
4. SQLite 벡터 검색은 Python/SQLite 확장 로딩 환경에 의존한다.

## 예시

```python
from base_template.integrations.db import DBClient
from base_template.integrations.db.engines.sqlite import SQLiteEngine
from base_template.integrations.db.base import CollectionSchema, ColumnSpec, Document

engine = SQLiteEngine(database_path="data/db/playground.sqlite")
client = DBClient(engine)
client.connect()

schema = CollectionSchema(
    name="items",
    primary_key="doc_id",
    payload_field="payload",
    columns=[
        ColumnSpec(name="doc_id", data_type="TEXT", is_primary=True),
        ColumnSpec(name="payload", data_type="TEXT"),
    ],
)
client.create_collection(schema)
client.upsert("items", [Document(doc_id="1", payload={"name": "A"})])

client.close()
```
