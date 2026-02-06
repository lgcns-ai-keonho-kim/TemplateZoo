# DB 통합 가이드

이 문서는 `src/base_template/integrations/db` 모듈의 설계와 사용 방법을 설명합니다. 대상 독자는 백엔드 경력 3년 이하 개발자입니다.

**구성 요소**

- 엔진 인터페이스: `BaseDBEngine`
- 공통 모델: `CollectionSchema`, `Document`, `Query`, `VectorSearchRequest`
- 클라이언트 파사드: `DBClient`
- DSL 빌더: `ReadBuilder`, `WriteBuilder`, `DeleteBuilder`
- 엔진 구현체: SQLite, Redis, Elasticsearch, MongoDB, Postgres

## 핵심 개념

- 컬렉션 스키마: 컬렉션(테이블/인덱스)의 구조와 벡터 필드를 정의합니다.
- 문서 모델: 공통 문서 구조로 저장/조회에 사용합니다.
- 필드 출처: `FieldSource`로 컬럼/페이로드 구분을 결정합니다.
- 벡터 검색: `VectorSearchRequest` 기반으로 엔진별 벡터 검색을 수행합니다.

## 스키마 설계 규칙

- `primary_key`는 문서 ID에 매핑됩니다.
- `payload_field`가 있으면 `Document.payload`가 해당 필드에 JSON으로 저장됩니다.
- `payload_field`가 없으면 `Document.fields`가 곧 저장 데이터입니다.
- `vector_field`가 정의되면 벡터 검색이 활성화됩니다.
- `CollectionSchema.validate_document/validate_query`가 스키마 위반을 사전에 차단합니다.

## 동작 흐름

1. 엔진 생성 및 연결
2. 스키마 정의 및 컬렉션 생성
3. 문서 업서트
4. 조회/삭제/벡터 검색

```python
from base_template.integrations.db import DBClient
from base_template.integrations.db.engines.sqlite import SqliteVectorEngine
from base_template.integrations.db.base import CollectionSchema, ColumnSpec, Document, Vector, VectorSearchRequest

engine = SqliteVectorEngine(database_path="data/db/app.sqlite")
client = DBClient(engine)
client.connect()

schema = CollectionSchema(
    name="items",
    primary_key="doc_id",
    payload_field="payload",
    vector_field="embedding",
    vector_dimension=3,
    columns=[
        ColumnSpec(name="doc_id", data_type="TEXT", is_primary=True),
        ColumnSpec(name="payload", data_type="TEXT"),
        ColumnSpec(name="embedding", is_vector=True, dimension=3),
    ],
)
client.create_collection(schema)

client.upsert(
    "items",
    [
        Document(doc_id="1", payload={"title": "A"}, vector=Vector(values=[0.1, 0.2, 0.3])),
        Document(doc_id="2", payload={"title": "B"}, vector=Vector(values=[0.0, 0.1, 0.0])),
    ],
)

rows = client.read("items").where_payload("title").eq("A").fetch()

vector_request = VectorSearchRequest(
    collection="items",
    vector=Vector(values=[0.1, 0.2, 0.3]),
    top_k=3,
    include_vectors=False,
)
vector_results = client.vector_search(vector_request)

client.close()
```

## DSL 빌더 사용법

- `ReadBuilder`: `where()`로 조건을 쌓고 `fetch()`로 결과를 가져옵니다.
- `WriteBuilder`: `upsert()`/`upsert_one()`으로 저장합니다.
- `DeleteBuilder`: `by_id()` 또는 조건 기반 `execute()`를 사용합니다.

```python
rows = (
    client.read("items")
    .where_payload("category").eq("book")
    .order_by_payload("price").asc()
    .limit(10)
    .fetch()
)

client.delete("items").by_id("1")
```

## 벡터 검색 호출 방법

- `ReadBuilder`는 현재 `vector()` 체이닝을 노출하지 않습니다.
- 벡터 검색은 `VectorSearchRequest`를 만들고 `DBClient.vector_search()`를 호출합니다.

```python
from base_template.integrations.db.base import Vector, VectorSearchRequest

request = VectorSearchRequest(
    collection="items",
    vector=Vector(values=[0.05, 0.2, 0.4]),
    top_k=5,
)
response = client.vector_search(request)
```

## Elasticsearch 주의 사항

- Elasticsearch는 **근실시간(NRT)** 특성상 색인 직후 검색이 반영되지 않을 수 있습니다.
- 테스트/즉시 조회가 필요하면 `refresh_collection()`을 호출하세요.

```python
engine.refresh_collection("items")
```

- 문자열 정확 일치 조건은 `field`와 `field.keyword`를 함께 조회해 정확도를 높입니다.

### HTTPS/TLS 설정

Elasticsearch가 HTTPS로 동작하면 CA 인증서를 설정해야 합니다.

환경 변수 예시:

```
ELASTICSEARCH_SCHEME=https
ELASTICSEARCH_HOST=127.0.0.1
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PW=elastic
ELASTICSEARCH_CA_CERTS=certs/http_ca.crt
ELASTICSEARCH_VERIFY_CERTS=true
# ELASTICSEARCH_SSL_FINGERPRINT=AA:BB:CC:...
```

코드 주입 예시:

```python
from base_template.integrations.db.engines.elasticsearch import ElasticSearchEngine

engine = ElasticSearchEngine(
    host="127.0.0.1",
    port=9200,
    scheme="https",
    user="elastic",
    password="elastic",
    ca_certs="certs/http_ca.crt",
    verify_certs=True,
)
```

## SQLite 벡터 테스트 주의 사항

- sqlite-vec 확장 로딩이 가능한 Python 빌드가 필요합니다.
- `pyenv`를 사용할 때는 다음 명령으로 빌드합니다.

```bash
PYTHON_CONFIGURE_OPTS="--enable-loadable-sqlite-extensions" pyenv install 3.13.9
pyenv local 3.13.9
```

## PostgreSQL/PGVector 설정

PGVector는 **DB마다 확장을 활성화**해야 합니다.

```bash
sudo -u postgres psql -d playground
```

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## MongoDB 인증 팁

- `MONGODB_DB`는 기본 데이터베이스이며, 인증 DB도 기본적으로 이 값을 사용합니다.
- 인증 DB가 다른 경우 `MONGODB_AUTH_DB`를 지정하세요.

```env
MONGODB_DB=playground
MONGODB_AUTH_DB=admin
```

## Ollama 임베딩 테스트 안내

- 벡터 테스트는 **Ollama 임베딩 모델을 하드코딩**해서 사용합니다.
- 기본 모델: `embeddinggemma:300m-qat-q8_0`
- 기본 접속 URL: `http://127.0.0.1:11434`
- 설정 위치: `tests/conftest.py`

필요 시 `tests/conftest.py`에서 모델명/URL을 수정하세요.

## 엔진별 지원 요약

| 엔진 | CRUD | 필터/정렬 | 벡터 검색 | 비고 |
| --- | --- | --- | --- | --- |
| SQLite | 지원 | 지원 | 지원 | `sqlite-vec` 필요 |
| Redis | 지원 | 제한적 | 지원 | 인덱스 없음, 전체 스캔 |
| Elasticsearch | 지원 | 지원 | 지원 | 컬럼 삭제 불가 |
| MongoDB | 지원 | 지원 | 미지원 | 벡터 DB 미사용 가정 |
| Postgres | 지원 | 지원 | 지원 | PGVector 필요 |

## 제약 사항

- SQLite/Postgres는 식별자 형식이 엄격하며 유효하지 않으면 예외가 발생합니다.
- Redis는 인덱스 없이 스캔 기반이라 대규모 데이터에서 성능이 떨어질 수 있습니다.
- Elasticsearch는 컬럼 삭제를 지원하지 않아 재색인이 필요합니다.
- MongoDB는 벡터 검색을 제공하지 않습니다.

## 확장 포인트

- 새 DB 엔진 추가는 `BaseDBEngine` 구현체로 분리합니다.
- `CollectionSchema`를 확장해 표준 필드와 메타데이터를 추가할 수 있습니다.
