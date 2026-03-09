# db/engines/sql_common.md

소스 경로: `src/text_to_sql/integrations/db/engines/sql_common.py`

## 1. 역할

- 목적: SQL 계열 엔진에서 공통으로 사용하는 유틸리티를 제공한다.
- 설명: 스키마 보정, 필드 출처 결정, 컬럼 선택, 식별자 인용 로직을 통합한다.
- 디자인 패턴: 유틸리티 모듈

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `SQLIdentifierHelper` | `quote_identifier, quote_table, plain_identifier` |

### 2-2. 함수

- `ensure_schema`
- `resolve_source`
- `select_columns`
- `select_sql`
- `payload_field`
- `vector_field`
- `vector_dimension`

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 연관 모듈

- `src/text_to_sql/integrations/db/base/models.py`
