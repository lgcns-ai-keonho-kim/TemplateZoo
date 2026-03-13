# RedisFilterEvaluator 가이드

이 문서는 `src/rag_chatbot/integrations/db/engines/redis/filter_evaluator.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

공통 필터 표현식을 백엔드 질의식으로 변환하거나 메모리 내 보완 평가를 담당한다.

## 2. 공개 구성

- 클래스 `RedisFilterEvaluator`
  공개 메서드: `match`

## 3. 코드 설명

- 공통 `FilterExpression`을 백엔드별 표현으로 바꾸거나, 필요한 경우 메모리 내에서 최종 보정한다.

## 4. 유지보수/추가개발 포인트

- 이 모듈은 같은 엔진 폴더의 `engine.py`와 짝을 이루므로, 내부 표현을 바꾸면 호출자와 반환 형식을 함께 점검해야 한다.
- 스키마 변경이나 필드명 변경이 생기면 mapper, schema manager, filter 계층을 동시에 확인해야 한다.

## 5. 관련 문서

- `docs/integrations/overview.md`
- `docs/integrations/db/README.md`
