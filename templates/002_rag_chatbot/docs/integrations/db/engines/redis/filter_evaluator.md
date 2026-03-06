# filter_evaluator 모듈

이 문서는 `src/rag_chatbot/integrations/db/engines/redis/filter_evaluator.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

Redis 필터 평가기를 제공한다.

## 2. 설명

쿼리 필터 조건을 문서에 적용해 일치 여부를 반환한다.

## 3. 디자인 패턴

전략 패턴

## 4. 주요 구성

- 클래스 `RedisFilterEvaluator`
  주요 메서드: `match`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/engines/redis/engine.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
