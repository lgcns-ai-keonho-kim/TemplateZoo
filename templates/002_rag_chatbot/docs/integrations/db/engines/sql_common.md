# sql_common 모듈

이 문서는 `src/rag_chatbot/integrations/db/engines/sql_common.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

SQL 계열 엔진에서 공통으로 사용하는 유틸리티를 제공한다.

## 2. 설명

스키마 보정, 필드 출처 결정, 컬럼 선택, 식별자 인용 로직을 통합한다.

## 3. 디자인 패턴

유틸리티 모듈

## 4. 주요 구성

- 클래스 `SQLIdentifierHelper`
  주요 메서드: `quote_identifier`, `quote_table`, `plain_identifier`
- 함수 `ensure_schema`
- 함수 `resolve_source`
- 함수 `select_columns`
- 함수 `select_sql`
- 함수 `payload_field`
- 함수 `vector_field`
- 함수 `vector_dimension`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/base/models.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
