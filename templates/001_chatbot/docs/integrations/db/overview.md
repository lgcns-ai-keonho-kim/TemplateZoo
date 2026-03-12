# Integrations DB 모듈 레퍼런스

`src/chatbot/integrations/db`는 공통 DB 계약 위에 여러 엔진 구현을 올려서 상위 계층이 엔진 교체 비용을 낮출 수 있게 만든 계층이다.

## 1. 현재 기본 런타임과 선택 확장 경로

| 구분 | 현재 상태 | 코드 기준 |
| --- | --- | --- |
| 기본 저장소 | SQLite | `ChatHistoryRepository(db_client=None)`가 `SQLiteEngine` 생성 |
| 선택 확장 | PostgreSQL, MongoDB, Redis, Elasticsearch, LanceDB | 별도 조립 또는 테스트/실험 경로 |

현재 `src/chatbot/api/chat/services/runtime.py`는 기본 `ChatHistoryRepository`만 생성하므로, 실제 서비스 경로에서는 SQLite가 기본이다.

## 2. 계층 구조

| 경로 | 역할 |
| --- | --- |
| `base` | 엔진/세션/모델/쿼리 계약 |
| `client.py` | `DBClient` 퍼사드 |
| `query_builder` | 읽기/쓰기/삭제 DSL |
| `engines/*` | 엔진별 연결, 스키마, 변환, 검색 구현 |

## 3. 코드 설명

1. `DBClient`는 스키마 등록, CRUD, 벡터 검색을 공통 인터페이스로 묶는다.
2. `CollectionSchema`, `Query`, `VectorSearchRequest` 같은 공통 모델이 엔진 간 계약의 중심이다.
3. 엔진별 디렉터리는 연결, 스키마, 문서 변환, 필터/조건 빌드 책임을 분리해 둔다.
4. 벡터 검색 지원 여부는 엔진 능력 플래그와 스키마의 vector 필드 정의를 함께 본다.

## 4. 유지보수 포인트

1. `Query`와 `CollectionSchema` 의미를 바꾸면 모든 엔진 문서를 함께 수정해야 한다.
2. 기본 저장소가 SQLite라는 점은 setup 문서와 overview 문서에서 계속 분리해 설명해야 한다.
3. 엔진별 예외 메시지나 능력 차이를 감추기보다, 문서에서 제한사항을 명시하는 편이 유지보수에 유리하다.

## 5. 추가 개발과 확장 시 주의점

1. 새 엔진을 추가하려면 `BaseDBEngine` 구현, export, setup 문서, overview 문서 갱신이 함께 필요하다.
2. 새 엔진을 코드에만 추가해도 실제 서비스에서 사용되지는 않으므로 `runtime.py` 조립 변경 여부를 따로 결정해야 한다.
3. 벡터 검색 엔진을 붙일 때는 차원 정보, 거리 기준, payload 구조를 공통 계약과 맞춰야 한다.

## 6. 상세 문서

- `docs/integrations/db/client.md`
- `docs/integrations/db/base/engine.md`
- `docs/integrations/db/base/models.md`
- `docs/integrations/db/base/pool.md`
- `docs/integrations/db/base/query_builder.md`
- `docs/integrations/db/base/session.md`
- `docs/integrations/db/query_builder/read_builder.md`
- `docs/integrations/db/query_builder/write_builder.md`
- `docs/integrations/db/query_builder/delete_builder.md`
- `docs/integrations/db/engines/sqlite/engine.md`
- `docs/integrations/db/engines/postgres/engine.md`
- `docs/integrations/db/engines/mongodb/engine.md`
- `docs/integrations/db/engines/redis/engine.md`
- `docs/integrations/db/engines/elasticsearch/engine.md`
- `docs/integrations/db/engines/lancedb/engine.md`
