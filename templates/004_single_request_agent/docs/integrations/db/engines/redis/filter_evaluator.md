# Filter Evaluator

## 개요

`src/single_request_agent/integrations/db/engines/redis/filter_evaluator.py` 구현을 기준으로 현재 동작을 정리한다.

- Redis 필터 평가기를 제공한다.
- 쿼리 필터 조건을 문서에 적용해 일치 여부를 반환한다.
- 구현 형태: 전략 패턴

## 주요 구성

- 클래스: `RedisFilterEvaluator`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_agent/integrations/db/engines/redis/engine.py`
