# db/engines/redis/vector_scorer.md

소스 경로: `src/text_to_sql/integrations/db/engines/redis/vector_scorer.py`

## 1. 역할

- Redis 벡터 유사도 계산기를 제공한다.
- 코사인 유사도 기반 점수를 계산한다.
- 내부 구조는 유틸리티 클래스 기반이다.

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `RedisVectorScorer` | `cosine_similarity` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 관련 코드

- `src/text_to_sql/integrations/db/engines/redis/engine.py`
