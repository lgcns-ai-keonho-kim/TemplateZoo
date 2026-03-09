# db/engines/postgres/schema_manager.md

소스 경로: `src/text_to_sql/integrations/db/engines/postgres/schema_manager.py`

## 1. 역할

- 목적: PostgreSQL 스키마 관리 모듈을 제공한다.
- 설명: 테이블 생성/삭제와 컬럼 추가/삭제를 담당한다.
- 디자인 패턴: 매니저 패턴

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `PostgresSchemaManager` | `__init__, create_collection, delete_collection, add_column, drop_column` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 연관 모듈

- `src/text_to_sql/integrations/db/engines/postgres/vector_store.py`
- `src/text_to_sql/integrations/db/base/models.py`
- `src/text_to_sql/integrations/db/engines/sql_common.py`
