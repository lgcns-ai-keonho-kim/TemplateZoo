# Connection

## 개요

`src/one_shot_agent/integrations/db/engines/sqlite/connection.py` 구현을 기준으로 현재 동작을 정리한다.

- SQLite 연결 관리 모듈을 제공한다.
- 연결 초기화/종료와 PRAGMA 적용을 담당한다.
- 구현 형태: 매니저 패턴

## 주요 구성

- 클래스: `SqliteConnectionManager`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/one_shot_agent/integrations/db/engines/sqlite/engine.py`
