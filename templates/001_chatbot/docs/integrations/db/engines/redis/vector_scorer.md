# `db/engines/redis/vector_scorer.py` 레퍼런스

## 1. 모듈 목적

- 목적: Redis 벡터 유사도 계산기를 제공한다.
- 설명: 코사인 유사도 기반 점수를 계산한다.
- 디자인 패턴: 유틸리티 클래스

## 2. 핵심 심볼

- `class RedisVectorScorer`

## 3. 입력/출력 관점

- 벡터 필드 저장/인덱싱/유사도 계산 보조 로직을 담당한다.
- 소스 경로: `src/chatbot/integrations/db/engines/redis/vector_scorer.py`
- 문서 경로: `docs/integrations/db/engines/redis/vector_scorer.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/db/engines/redis/engine.py`

## 6. 변경 영향 범위

- 벡터 처리 로직 변경 시 검색 품질, 성능, 인덱스 호환성에 영향을 준다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
