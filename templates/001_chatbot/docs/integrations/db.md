# Integrations DB 레퍼런스

이 문서는 `src/chatbot/integrations/db`의 공통 인터페이스, Query DSL, 엔진별 차이, 교체 절차를 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| BaseDBEngine | 모든 DB 엔진이 구현해야 하는 인터페이스 | `base/engine.py` |
| DBClient | 엔진 호출을 단일 API로 감싸는 퍼사드 | `client.py` |
| CollectionSchema | 컬렉션 구조 정의 | `base/models.py` |
| Document | 저장/조회 단위 데이터 모델 | `base/models.py` |
| Query | 필터/정렬/페이지네이션 모델 | `base/models.py` |
| VectorSearchRequest | 벡터 검색 요청 모델 | `base/models.py` |

## 2. 관련 스크립트

| 분류 | 파일 | 역할 |
| --- | --- | --- |
| 공개 API | `src/chatbot/integrations/db/__init__.py` | DBClient/Builder/Engine 노출 |
| 클라이언트 | `src/chatbot/integrations/db/client.py` | 연결, 스키마 등록, CRUD, 벡터 검색 호출 |
| 베이스 인터페이스 | `src/chatbot/integrations/db/base/engine.py` | 엔진 공통 메서드 |
| 베이스 모델 | `src/chatbot/integrations/db/base/models.py` | Schema/Document/Query/Vector 모델 |
| SQLite 엔진 | `src/chatbot/integrations/db/engines/sqlite/engine.py` | 로컬 기본 CRUD 엔진 |
| LanceDB 엔진 | `src/chatbot/integrations/db/engines/lancedb/engine.py` | 로컬 벡터 검색 엔진 |
| Postgres 엔진 | `src/chatbot/integrations/db/engines/postgres/engine.py` | PostgreSQL + pgvector |
| Redis 엔진 | `src/chatbot/integrations/db/engines/redis/engine.py` | Redis 기반 저장/검색 |
| MongoDB 엔진 | `src/chatbot/integrations/db/engines/mongodb/engine.py` | MongoDB CRUD |
| Elasticsearch 엔진 | `src/chatbot/integrations/db/engines/elasticsearch/engine.py` | ES 검색/벡터 검색 |

## 3. 핵심 인터페이스

1. 연결 수명주기: `connect`, `close`
2. 스키마 관리: `create_collection`, `delete_collection`, `add_column`, `drop_column`
3. 데이터 처리: `upsert`, `get`, `delete`, `query`
4. 벡터 검색: `vector_search`
5. 속성: `name`, `supports_vector_search`

## 4. Query DSL 기준

예시:

```python
query = (
    QueryBuilder()
    .where_column("session_id").eq("abc")
    .order_by_column("updated_at").desc()
    .limit(20)
    .offset(0)
    .build()
)
```

지원 연산:

1. 비교: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`
2. 집합: `in_`, `not_in`
3. 포함: `contains`
4. 논리: `and_`, `or_`
5. 정렬: `order_by`, `asc`, `desc`
6. 페이징: `limit`, `offset`
7. 벡터: `vector`, `top_k`, `include_vectors`

## 5. 엔진별 비교

| 엔진 | 클래스 | 벡터 검색 | 기본 특성 |
| --- | --- | --- | --- |
| SQLite | `SQLiteEngine` | 미지원 | 기본 Chat 저장소, 벡터 검색 호출 시 오류 |
| LanceDB | `LanceDBEngine` | 지원 | 로컬 벡터 검색 실험/검증에 적합 |
| PostgreSQL | `PostgresEngine` | 지원 | pgvector 연동 기반 |
| Redis | `RedisEngine` | 조건부 지원 | `enable_vector=False` 기본 |
| MongoDB | `MongoDBEngine` | 미지원 | CRUD 중심 |
| Elasticsearch | `ElasticsearchEngine` | 지원 | `knn` 기반 검색 |

엔진별 주의점:

1. Elasticsearch는 TLS 설정(`ca_certs`, `verify_certs`)이 잘못되면 연결 단계에서 실패한다.
2. Elasticsearch CA 파일 권한 부족 시 `SSLError([Errno 13] Permission denied)`가 발생할 수 있다.
3. MongoDB는 `authSource` 불일치 시 `AuthenticationFailed`가 발생한다.
4. SQLite는 벡터 검색 미지원이 기본 정책이다.

## 6. 실제 연결 경로

Chat 기본 경로:

1. `ChatHistoryRepository`가 기본적으로 SQLite 저장소를 사용
2. `DBClient(engine)`를 통해 CRUD 수행
3. `shared/chat/services/chat_service.py`가 저장소를 사용

교체 경로:

1. `api/chat/services/runtime.py`에서 엔진/저장소 조립 변경
2. `ChatHistoryRepository(db_client=...)` 주입

## 7. 교체 절차

### 7-1. LanceDB로 벡터 검색 구성

1. `LanceDBEngine(uri=...)` 생성
2. `DBClient(lancedb_engine)` 생성
3. `vector_field`, `vector_dimension`이 포함된 컬렉션 스키마 사용

### 7-2. PostgreSQL로 교체

1. `PostgresEngine` 생성
2. `DBClient(postgres_engine)` 생성
3. `ChatHistoryRepository(db_client=...)` 주입

### 7-3. Elasticsearch로 교체

1. TLS 검증 정책(`ca_certs`, 지문)을 먼저 확정
2. 인덱스 매핑/벡터 필드 차원 정책 확정
3. 컬럼 삭제 대신 reindex 전략 준비

## 8. 트러블슈팅

| 증상 | 원인 후보 | 확인 스크립트 | 조치 |
| --- | --- | --- | --- |
| 벡터 검색 호출 즉시 실패 | 벡터 필드 미정의 또는 엔진 미지원 | `client.py`, engine `supports_vector_search` | 스키마/엔진 정책 점검 |
| Mongo 인증 실패(`Authentication failed`) | `authSource`/계정 DB 불일치 | `.env`, Mongo 사용자 정의 | `MONGODB_AUTH_DB` 재설정 |
| Elasticsearch TLS 실패(`CERTIFICATE_VERIFY_FAILED`) | CA 누락/오경로 | `ELASTICSEARCH_CA_CERTS` | CA 경로 교정 |
| Elasticsearch TLS 실패(`Permission denied`) | CA 파일 권한 부족 | `ls -l`, `namei -l` | 파일 읽기 권한 부여 |
| Elasticsearch 컬럼 삭제 오류 | 엔진 제약 | `elasticsearch/engine.py` | reindex 방식 사용 |

## 9. 관련 문서

- `docs/integrations/overview.md`
- `docs/setup/sqlite.md`
- `docs/setup/lancedb.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/setup/mongodb.md`
- `docs/setup/troubleshooting.md`
