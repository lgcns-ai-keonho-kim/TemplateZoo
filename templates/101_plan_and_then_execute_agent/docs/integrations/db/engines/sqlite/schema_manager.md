# Schema Manager 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/engines/sqlite/schema_manager.py`

## 역할

- 목적: SQLite 스키마 관리 모듈을 제공한다.
- 설명: 컬렉션 생성/삭제와 컬럼 추가/삭제를 담당한다.
- 디자인 패턴: 매니저 패턴

## 주요 구성

- 클래스: `SqliteSchemaManager`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/engines/sqlite/engine.py`
