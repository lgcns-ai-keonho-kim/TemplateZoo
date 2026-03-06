# Vector Scorer 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/engines/redis/vector_scorer.py`

## 역할

- 목적: Redis 벡터 유사도 계산기를 제공한다.
- 설명: 코사인 유사도 기반 점수를 계산한다.
- 디자인 패턴: 유틸리티 클래스

## 주요 구성

- 클래스: `RedisVectorScorer`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/engines/redis/engine.py`
