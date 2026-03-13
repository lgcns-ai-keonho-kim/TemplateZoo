# db/engines/redis/document_mapper.md

소스 경로: `src/text_to_sql/integrations/db/engines/redis/document_mapper.py`

## 1. 역할

- Redis 문서 매퍼 모듈을 제공한다.
- Document 모델과 Redis Hash 데이터 간 변환을 담당한다.
- 내부 구조는 매퍼 패턴 기반이다.

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `RedisDocumentMapper` | `__init__, to_hash_mapping, from_hash` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 관련 코드

- `src/text_to_sql/integrations/db/base/models.py`
- `src/text_to_sql/integrations/db/engines/redis/keyspace.py`
