# db/base/query_builder.md

소스 경로: `src/text_to_sql/integrations/db/base/query_builder.py`

## 1. 역할

- 공통 DSL 기반 QueryBuilder를 제공한다.
- 체이닝 방식으로 Filter/Sort/Pagination을 구성해 Query 모델을 생성한다.
- 내부 구조는 빌더 패턴 기반이다.

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `QueryBuilder` | `__init__, where, where_column, where_payload, and_, or_, eq, ne, ...` |
| `AggregateQueryBuilder` | `__init__, where, where_column, where_payload, and_, or_, eq, ne, ...` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 관련 코드

- `src/text_to_sql/integrations/db/base/models.py`
