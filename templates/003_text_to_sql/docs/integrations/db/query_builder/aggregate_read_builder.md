# db/query_builder/aggregate_read_builder.md

소스 경로: `src/text_to_sql/integrations/db/query_builder/aggregate_read_builder.py`

## 1. 역할

- 목적: 집계 조회 전용 DSL 빌더를 제공한다.
- 설명: AggregateQueryBuilder를 감싸 체이닝 후 fetch()로 집계 조회를 수행한다.
- 디자인 패턴: 빌더 패턴

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `AggregateReadBuilder` | `__init__, where, where_column, where_payload, and_, or_, eq, ne, ...` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 연관 모듈

- `src/text_to_sql/integrations/db/base/query_builder.py`
- `src/text_to_sql/integrations/db/base/engine.py`
- `src/text_to_sql/integrations/db/base/models.py`
