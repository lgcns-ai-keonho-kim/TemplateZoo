# db/engines/redis/keyspace.md

소스 경로: `src/text_to_sql/integrations/db/engines/redis/keyspace.py`

## 1. 역할

- 목적: Redis 키스페이스 유틸 모듈을 제공한다.
- 설명: 키 생성 규칙과 SCAN 기반 키 수집을 담당한다.
- 디자인 패턴: 유틸리티 클래스

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `RedisKeyspaceHelper` | `payload_storage_key, make_key, scan_keys` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 연관 모듈

- `src/text_to_sql/integrations/db/engines/redis/engine.py`
- `src/text_to_sql/integrations/db/base/models.py`
