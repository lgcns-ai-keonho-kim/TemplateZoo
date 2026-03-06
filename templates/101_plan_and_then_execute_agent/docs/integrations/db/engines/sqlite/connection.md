# Connection 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/engines/sqlite/connection.py`

## 역할

- 목적: SQLite 연결 관리 모듈을 제공한다.
- 설명: 연결 초기화/종료와 PRAGMA 적용을 담당한다.
- 디자인 패턴: 매니저 패턴

## 주요 구성

- 클래스: `SqliteConnectionManager`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/engines/sqlite/engine.py`
