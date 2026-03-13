# db/engines/lancedb/schema_adapter.md

소스 경로: `src/text_to_sql/integrations/db/engines/lancedb/schema_adapter.py`

## 1. 역할

- LanceDB 스키마/행 변환 어댑터를 제공한다.
- CollectionSchema를 PyArrow 스키마로 변환하고, 입력 row를 스키마 타입으로 정규화한다.
- 내부 구조는 어댑터 패턴 기반이다.

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `LanceSchemaAdapter` | `build_arrow_schema, build_arrow_field, normalize_row` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 관련 코드

- `src/text_to_sql/integrations/db/base/models.py`
- `src/text_to_sql/integrations/db/engines/sql_common.py`
