# Schema Manager 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/engines/postgres/schema_manager.py`

## 역할

- 목적: PostgreSQL 스키마 관리 모듈을 제공한다.
- 설명: 테이블 생성/삭제와 컬럼 추가/삭제를 담당한다.
- 디자인 패턴: 매니저 패턴

## 주요 구성

- 클래스: `PostgresSchemaManager`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/engines/postgres/vector_store.py`
