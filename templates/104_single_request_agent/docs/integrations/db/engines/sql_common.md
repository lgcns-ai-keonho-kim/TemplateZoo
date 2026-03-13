# SQL Common

## 개요

`src/single_request_agent/integrations/db/engines/sql_common.py` 구현을 기준으로 현재 동작을 정리한다.

- SQL 계열 엔진에서 공통으로 사용하는 유틸리티를 제공한다.
- 스키마 보정, 필드 출처 결정, 컬럼 선택, 식별자 인용 로직을 통합한다.
- 구현 형태: 유틸리티 모듈

## 주요 구성

- 클래스: `SQLIdentifierHelper`
- 함수: `ensure_schema`, `resolve_source`, `select_columns`, `select_sql`, `payload_field`, `vector_field`, `vector_dimension`

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_agent/integrations/db/base/models.py`
