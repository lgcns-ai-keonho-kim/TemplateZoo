# db/engines/postgres/vector_store.md

소스 경로: `src/text_to_sql/integrations/db/engines/postgres/vector_store.py`

## 1. 역할

- PostgreSQL 벡터 관리 모듈을 제공한다.
- PGVector 확장/인덱스 생성과 벡터 컬럼 유효성 판단을 담당한다.
- 내부 구조는 매니저 패턴 기반이다.

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `PostgresVectorStore` | `__init__, adapter, has_vector_column, ensure_vector_extension, ensure_vector_index, drop_vector_index_if_needed` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 관련 코드

- `src/text_to_sql/integrations/db/engines/postgres/vector_adapter.py`
- `src/text_to_sql/integrations/db/base/models.py`
- `src/text_to_sql/integrations/db/engines/sql_common.py`
