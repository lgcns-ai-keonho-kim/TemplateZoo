# Filter Evaluator 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/engines/redis/filter_evaluator.py`

## 역할

- 목적: Redis 필터 평가기를 제공한다.
- 설명: 쿼리 필터 조건을 문서에 적용해 일치 여부를 반환한다.
- 디자인 패턴: 전략 패턴

## 주요 구성

- 클래스: `RedisFilterEvaluator`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/engines/redis/engine.py`
