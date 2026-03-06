# Models Query 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/base/_models_query.py`

## 역할

- 목적: DB 조회 모델 공개 API 파사드를 제공한다.
- 설명: 정렬/페이지네이션/조회 모델 분리 구현을 재노출한다.
- 디자인 패턴: 퍼사드

## 주요 구성

- 클래스: 없음
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/_sort_order.py`
- `src/plan_and_then_execute_agent/integrations/db/base/_query.py`
