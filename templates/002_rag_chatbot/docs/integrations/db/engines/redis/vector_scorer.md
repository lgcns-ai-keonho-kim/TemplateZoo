# RedisVectorScorer 가이드

이 문서는 `src/rag_chatbot/integrations/db/engines/redis/vector_scorer.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

벡터 컬럼, 거리 계산, 인덱스 또는 점수 해석과 관련된 전용 유틸리티를 제공한다.

## 2. 공개 구성

- 클래스 `RedisVectorScorer`
  공개 메서드: `cosine_similarity`

## 3. 코드 설명

- 벡터 차원, 거리 메트릭, 인덱스 생성 규칙을 한곳에 모아 검색 정책 변경 영향을 줄인다.

## 4. 유지보수/추가개발 포인트

- 이 모듈은 같은 엔진 폴더의 `engine.py`와 짝을 이루므로, 내부 표현을 바꾸면 호출자와 반환 형식을 함께 점검해야 한다.
- 스키마 변경이나 필드명 변경이 생기면 mapper, schema manager, filter 계층을 동시에 확인해야 한다.

## 5. 관련 문서

- `docs/integrations/overview.md`
- `docs/integrations/db/README.md`
