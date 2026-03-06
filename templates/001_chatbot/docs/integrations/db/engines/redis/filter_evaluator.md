# `db/engines/redis/filter_evaluator.py` 레퍼런스

## 1. 모듈 목적

- 목적: Redis 필터 평가기를 제공한다.
- 설명: 쿼리 필터 조건을 문서에 적용해 일치 여부를 반환한다.
- 디자인 패턴: 전략 패턴

## 2. 핵심 심볼

- `class RedisFilterEvaluator`

## 3. 입력/출력 관점

- Query 조건을 엔진 전용 필터/WHERE 조건으로 변환한다.
- 소스 경로: `src/chatbot/integrations/db/engines/redis/filter_evaluator.py`
- 문서 경로: `docs/integrations/db/engines/redis/filter_evaluator.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/db/engines/redis/engine.py`

## 6. 변경 영향 범위

- 조건 변환 로직 변경 시 검색 정확도와 결과 집합이 달라질 수 있다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
