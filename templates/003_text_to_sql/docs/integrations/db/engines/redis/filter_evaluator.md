# db/engines/redis/filter_evaluator.md

소스 경로: `src/text_to_sql/integrations/db/engines/redis/filter_evaluator.py`

## 1. 역할

- 목적: Redis 필터 평가기를 제공한다.
- 설명: 쿼리 필터 조건을 문서에 적용해 일치 여부를 반환한다.
- 디자인 패턴: 전략 패턴

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `RedisFilterEvaluator` | `match` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 연관 모듈

- `src/text_to_sql/integrations/db/engines/redis/engine.py`
- `src/text_to_sql/integrations/db/base/models.py`
