# Integrations DB 가이드

이 문서는 `src/rag_chatbot/integrations/db`의 공통 인터페이스, Query DSL, 엔진별 차이, 교체 절차를 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| BaseDBEngine | 모든 DB 엔진이 구현해야 하는 인터페이스 | `base/engine.py` |
| DBClient | 엔진 호출을 단일 API로 감싸는 퍼사드 | `client.py` |
| CollectionSchema | 컬렉션 구조(기본키/컬럼/벡터필드) 정의 | `base/models.py` |
| Document | 저장/조회 단위 데이터 모델 | `base/models.py` |
| Query | 필터/정렬/페이지네이션 모델 | `base/models.py` |
| QueryBuilder | 체이닝 DSL로 Query를 만드는 빌더 | `base/query_builder.py` |
| ReadBuilder | 읽기 전용 DSL 래퍼 | `query_builder/read_builder.py` |
| WriteBuilder | 쓰기 전용 DSL 래퍼 | `query_builder/write_builder.py` |
| DeleteBuilder | 삭제 전용 DSL 래퍼 | `query_builder/delete_builder.py` |
| VectorSearchRequest | 벡터 검색 요청 모델 | `base/models.py` |

## 2. 관련 스크립트

| 분류 | 파일 | 역할 |
| --- | --- | --- |
| 공개 API | `src/rag_chatbot/integrations/db/__init__.py` | DBClient/Builder/Engine 노출 |
| 클라이언트 | `src/rag_chatbot/integrations/db/client.py` | 엔진 연결, 스키마 등록, CRUD, 벡터 검색 호출 |
| 베이스 인터페이스 | `src/rag_chatbot/integrations/db/base/engine.py` | 엔진 공통 메서드 정의 |
| 베이스 모델 | `src/rag_chatbot/integrations/db/base/models.py` | Schema/Document/Query/Vector 모델 |
| 공통 DSL | `src/rag_chatbot/integrations/db/base/query_builder.py` | where/order/limit/vector DSL |
| 읽기 DSL | `src/rag_chatbot/integrations/db/query_builder/read_builder.py` | `fetch`, `fetch_vector` |
| 쓰기 DSL | `src/rag_chatbot/integrations/db/query_builder/write_builder.py` | `upsert`, `upsert_one` |
| 삭제 DSL | `src/rag_chatbot/integrations/db/query_builder/delete_builder.py` | `by_id`, `execute` |
| SQLite 엔진 | `src/rag_chatbot/integrations/db/engines/sqlite/engine.py` | 로컬 기본 엔진 |
| Postgres 엔진 | `src/rag_chatbot/integrations/db/engines/postgres/engine.py` | PostgreSQL + pgvector |
| Redis 엔진 | `src/rag_chatbot/integrations/db/engines/redis/engine.py` | Redis 기반 저장/검색 |
| MongoDB 엔진 | `src/rag_chatbot/integrations/db/engines/mongodb/engine.py` | MongoDB CRUD |
| Elasticsearch 엔진 | `src/rag_chatbot/integrations/db/engines/elasticsearch/engine.py` | ES 검색/벡터 검색 |

## 3. 핵심 인터페이스

## 3-1. BaseDBEngine 필수 메서드

1. 연결 수명주기: `connect`, `close`
2. 스키마 관리: `create_collection`, `delete_collection`, `add_column`, `drop_column`
3. 데이터 처리: `upsert`, `get`, `delete`, `query`
4. 벡터 검색: `vector_search`
5. 속성: `name`, `supports_vector_search`

## 3-2. DBClient 역할

1. 엔진 연결/종료를 직렬화 락으로 보호한다.
2. 컬렉션 스키마를 등록/조회한다.
3. Query 검증과 Document 검증을 수행한 뒤 엔진을 호출한다.
4. DSL 빌더(`read`, `write`, `delete`) 엔트리를 제공한다.
5. 벡터 검색 가능 여부와 스키마 벡터 필드를 사전 검증한다.

## 3-3. 모델 기본값

`Pagination` 기본값:

1. `limit=50`
2. `offset=0`

스키마/필드 검증:

1. 허용되지 않은 컬럼 저장 시 `ValueError`
2. 벡터 필드 미정의 상태에서 vector 저장 시 `ValueError`
3. payload 필드 미정의 상태에서 payload 필터/정렬 시 `ValueError`

## 4. Query DSL 규칙

## 4-1. 공통 빌더 패턴

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

## 4-2. ReadBuilder

1. `fetch()`는 일반 Query 조회를 수행한다.
2. 벡터 값을 설정한 상태에서 `fetch()` 호출 시 오류를 발생시킨다.
3. 벡터 검색은 `fetch_vector()` 또는 `fetch_with_scores()`를 사용한다.

## 4-3. WriteBuilder

1. `upsert(documents)` 다건 저장
2. `upsert_one(document)` 단건 저장
3. 스키마가 있으면 저장 전 문서를 검증한다.

## 4-4. DeleteBuilder

1. `by_id`, `by_ids`는 직접 삭제
2. `where...execute()`는 조건 조회 후 삭제
3. 반환값은 삭제 건수다.

## 5. 엔진별 비교

| 엔진 | 클래스 | 벡터 검색 | 기본 특성 |
| --- | --- | --- | --- |
| SQLite | `SQLiteEngine` | 조건부 지원 | `enable_vector=True` + `sqlite_vec` 사용 가능 시 벡터 검색 지원 |
| PostgreSQL | `PostgresEngine` | 지원 | pgvector 연동 전제, `supports_vector_search=True` |
| Redis | `RedisEngine` | 조건부 지원 | `enable_vector=False` 기본, true일 때 코사인 유사도 기반 검색 |
| MongoDB | `MongoDBEngine` | 미지원 | `supports_vector_search=False`, `vector_search`는 오류 반환 |
| Elasticsearch | `ElasticsearchEngine` | 지원 | `knn` 기반 검색, 컬럼 삭제 직접 미지원 |

엔진별 주의점:

1. Redis 엔진은 벡터 검색 시 filter_expression을 아직 지원하지 않는다.
2. Elasticsearch 엔진은 `drop_column` 호출 시 오류를 발생시킨다.
3. MongoDB 엔진은 벡터 검색을 비활성화한다.
4. SQLite 엔진은 vector 기능 비활성화 시 벡터 검색을 막는다.

## 6. 실제 연결 경로

Chat 기본 경로:

1. `ChatHistoryRepository`가 기본적으로 `SQLiteEngine`을 내부 생성
2. `DBClient(engine)`를 통해 CRUD 수행
3. `shared/chat/services/chat_service.py`가 저장소를 사용

교체 경로:

1. `api/chat/services/runtime.py`에서 엔진/저장소 조립 변경
2. `ChatHistoryRepository(db_client=...)` 주입

## 7. 교체 절차

## 7-1. PostgreSQL로 교체

1. `PostgresEngine` 생성
2. `DBClient(postgres_engine)` 생성
3. `ChatHistoryRepository(db_client=...)`로 주입
4. 앱 조립에서 기존 저장소를 교체

예시:

```python
from rag_chatbot.integrations.db import DBClient
from rag_chatbot.integrations.db.engines.postgres import PostgresEngine
from rag_chatbot.shared.chat import ChatHistoryRepository

engine = PostgresEngine(
    host="127.0.0.1",
    port=5432,
    user="postgres",
    password="postgres",
    database="playground",
)
repository = ChatHistoryRepository(db_client=DBClient(engine))
```

## 7-2. Redis로 교체

1. `RedisEngine(enable_vector=...)`로 기능 범위를 먼저 결정한다.
2. vector filter 미지원 제약을 서비스 레벨에서 허용 가능한지 확인한다.
3. 대량 scan 성능을 운영 환경에서 검증한다.

## 7-3. Elasticsearch로 교체

1. 인덱스 매핑 생성 규칙을 먼저 확정한다.
2. 컬럼 삭제 대신 reindex 전략을 준비한다.
3. `knn` 검색 필드와 차원 정책을 문서화한다.

## 8. 트러블슈팅

| 증상 | 원인 후보 | 확인 스크립트 | 조치 |
| --- | --- | --- | --- |
| 벡터 검색 호출 즉시 실패 | vector_field 미정의 또는 엔진 미지원 | `client.py`, 각 engine `supports_vector_search` | 스키마 벡터 필드/엔진 옵션 점검 |
| payload 필터 조회 실패 | payload_field 미정의 | `base/models.py` | 스키마 payload_field 설정 확인 |
| 조건 삭제가 예상보다 많이 삭제됨 | delete DSL 조건 구성 오류 | `delete_builder.py` | `build()` 결과 Query를 먼저 점검 |
| Redis 검색 느림 | 전체 키 scan 비용 | `redis/engine.py` | 키 설계/캐시/인덱스 전략 재검토 |
| Elasticsearch 컬럼 삭제 오류 | 엔진 제약 | `elasticsearch/engine.py` | reindex 방식으로 변경 |

## 9. 소스 매칭 점검 항목

1. 엔진 목록이 `engines/__init__.py` 노출 목록과 일치하는가
2. DSL 메서드 설명이 `read/write/delete_builder.py`와 일치하는가
3. pagination 기본값이 `base/models.py`와 일치하는가
4. 엔진 제약 설명이 각 `engine.py` 구현과 일치하는가
5. 문서 경로가 실제 `src/rag_chatbot/integrations/db` 구조와 일치하는가

## 10. 관련 문서

- `docs/integrations/overview.md`
- `docs/setup/sqlite_vec.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/setup/mongodb.md`
- `docs/shared/chat.md`
- `docs/api/overview.md`
