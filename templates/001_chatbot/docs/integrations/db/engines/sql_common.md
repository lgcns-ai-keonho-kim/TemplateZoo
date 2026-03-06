# `db/engines/sql_common.py` 레퍼런스

## 1. 모듈 목적

- 목적: SQL 계열 엔진에서 공통으로 사용하는 유틸리티를 제공한다.
- 설명: 스키마 보정, 필드 출처 결정, 컬럼 선택, 식별자 인용 로직을 통합한다.
- 디자인 패턴: 유틸리티 모듈

## 2. 핵심 심볼

- `class SQLIdentifierHelper`
- `def ensure_schema`
- `def resolve_source`
- `def select_columns`
- `def select_sql`
- `def payload_field`
- `def vector_field`
- `def vector_dimension`

## 3. 입력/출력 관점

- SQL 계열 엔진에서 공통으로 쓰는 식별자/컬럼/스키마 유틸 함수를 제공한다.
- 소스 경로: `src/chatbot/integrations/db/engines/sql_common.py`
- 문서 경로: `docs/integrations/db/engines/sql_common.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/db/base/models.py`

## 6. 변경 영향 범위

- 공통 SQL 유틸 변경 시 SQLite/Postgres 엔진 쿼리 생성 동작이 동시에 영향받는다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
