# Connection

## 개요

`src/single_request_tool_agent/integrations/db/engines/postgres/connection.py` 구현을 기준으로 현재 동작을 정리한다.

- PostgreSQL 연결 관리 모듈을 제공한다.
- 연결 초기화/종료와 PGVector 타입 등록을 담당한다.
- 구현 형태: 매니저 패턴

## 주요 구성

- 클래스: `PostgresConnectionManager`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_tool_agent/integrations/db/engines/postgres/engine.py`
