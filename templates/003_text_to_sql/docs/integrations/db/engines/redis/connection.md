# db/engines/redis/connection.md

소스 경로: `src/text_to_sql/integrations/db/engines/redis/connection.py`

## 1. 역할

- Redis 연결 관리 모듈을 제공한다.
- 연결 초기화/종료와 클라이언트 보장을 담당한다.
- 내부 구조는 매니저 패턴 기반이다.

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `RedisConnectionManager` | `__init__, connect, close, ensure_client` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 관련 코드

- `src/text_to_sql/integrations/db/engines/redis/engine.py`
- `src/text_to_sql/shared/logging/__init__.py`
