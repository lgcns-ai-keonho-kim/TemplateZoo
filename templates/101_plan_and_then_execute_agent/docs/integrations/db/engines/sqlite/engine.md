# Engine 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/engines/sqlite/engine.py`

## 역할

- 목적: SQLite 기반 DB 엔진을 제공한다.
- 설명: 컬렉션 스키마 기반 CRUD와 일반 조회를 지원한다.
- 디자인 패턴: 어댑터 패턴

## 주요 구성

- 클래스: `SQLiteEngine`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/engine.py`
