# SQLIdentifierHelper 가이드

이 문서는 `src/rag_chatbot/integrations/db/engines/sql_common.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

여러 SQL 계열 엔진이 함께 쓰는 식별자, 스키마, 벡터 필드 헬퍼를 제공한다.

## 2. 공개 구성

- 클래스 `SQLIdentifierHelper`
  공개 메서드: `quote_identifier`, `quote_table`, `plain_identifier`
- 함수 `ensure_schema`
- 함수 `resolve_source`
- 함수 `select_columns`
- 함수 `select_sql`
- 함수 `payload_field`
- 함수 `vector_field`
- 함수 `vector_dimension`

## 3. 코드 설명

- SQL 엔진 공통 유틸리티를 재사용하면 식별자 quoting과 벡터 필드 선택 규칙을 일관되게 유지할 수 있다.

## 4. 유지보수/추가개발 포인트

- 이 모듈을 확장할 때는 같은 계층의 이웃 모듈과 계약이 어디에서 맞물리는지 먼저 확인하는 편이 안전하다.

## 5. 관련 문서

- `docs/integrations/overview.md`
- `docs/integrations/db/README.md`
