# db/engines/redis/engine.md

소스 경로: `src/text_to_sql/integrations/db/engines/redis/engine.py`

## 1. 역할

- Redis 기반 DB 엔진을 제공한다.
- 스키마 기반 필드 저장과 간단한 검색을 지원한다.
- 내부 구조는 어댑터 패턴 기반이다.

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `RedisEngine` | `__init__, name, supports_vector_search, connect, close, create_collection, delete_collection, add_column, ...` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 관련 코드

- `src/text_to_sql/integrations/db/base/engine.py`
- `src/text_to_sql/shared/logging/__init__.py`
- `src/text_to_sql/integrations/db/base/models.py`
- `src/text_to_sql/integrations/db/engines/sql_common.py`
- `src/text_to_sql/integrations/db/engines/redis/connection.py`
- `src/text_to_sql/integrations/db/engines/redis/document_mapper.py`
- `src/text_to_sql/integrations/db/engines/redis/filter_evaluator.py`
- `src/text_to_sql/integrations/db/engines/redis/keyspace.py`
- `src/text_to_sql/integrations/db/engines/redis/vector_scorer.py`
