# vector_scorer 모듈

이 문서는 `src/rag_chatbot/integrations/db/engines/redis/vector_scorer.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

Redis 벡터 유사도 계산기를 제공한다.

## 2. 설명

코사인 유사도 기반 점수를 계산한다.

## 3. 디자인 패턴

유틸리티 클래스

## 4. 주요 구성

- 클래스 `RedisVectorScorer`
  주요 메서드: `cosine_similarity`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/engines/redis/engine.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
