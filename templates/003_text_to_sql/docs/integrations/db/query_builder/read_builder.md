# db/query_builder/read_builder.md

소스 경로: `src/text_to_sql/integrations/db/query_builder/read_builder.py`

## 1. 역할

- 읽기 전용 DSL 빌더를 제공한다.
- QueryBuilder를 감싸 체이닝 후 fetch()로 조회한다.
- 내부 구조는 빌더 패턴 기반이다.

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `ReadBuilder` | `__init__, where, where_column, where_payload, and_, or_, eq, ne, ...` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 관련 코드

- `src/text_to_sql/integrations/db/base/query_builder.py`
- `src/text_to_sql/integrations/db/base/engine.py`
- `src/text_to_sql/integrations/db/base/models.py`
