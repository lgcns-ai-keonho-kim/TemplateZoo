# Vector Scorer

## 개요

`src/one_shot_agent/integrations/db/engines/redis/vector_scorer.py` 구현을 기준으로 현재 동작을 정리한다.

- Redis 벡터 유사도 계산기를 제공한다.
- 코사인 유사도 기반 점수를 계산한다.
- 구현 형태: 유틸리티 클래스

## 주요 구성

- 클래스: `RedisVectorScorer`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/one_shot_agent/integrations/db/engines/redis/engine.py`
