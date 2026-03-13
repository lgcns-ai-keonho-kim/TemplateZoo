# db/engines/postgres/connection.md

소스 경로: `src/text_to_sql/integrations/db/engines/postgres/connection.py`

## 1. 역할

- PostgreSQL 연결 관리 모듈을 제공한다.
- 연결 초기화/종료와 PGVector 타입 등록을 담당한다.
- 내부 구조는 매니저 패턴 기반이다.

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `PostgresConnectionManager` | `__init__, connect, close, ensure_connection` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 관련 코드

- `src/text_to_sql/integrations/db/engines/postgres/engine.py`
- `src/text_to_sql/shared/logging/__init__.py`
- `src/text_to_sql/integrations/db/engines/postgres/vector_adapter.py`
