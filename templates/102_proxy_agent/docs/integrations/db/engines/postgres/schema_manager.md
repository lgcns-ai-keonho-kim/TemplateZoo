# Schema Manager

## 개요

`src/tool_proxy_agent/integrations/db/engines/postgres/schema_manager.py` 구현을 기준으로 현재 동작을 정리한다.

- PostgreSQL 스키마 관리 모듈을 제공한다.
- 테이블 생성/삭제와 컬럼 추가/삭제를 담당한다.
- 구현 형태: 매니저 패턴

## 주요 구성

- 클래스: `PostgresSchemaManager`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/tool_proxy_agent/integrations/db/engines/postgres/vector_store.py`
