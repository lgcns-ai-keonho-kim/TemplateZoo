# Sort Order 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/base/_sort_order.py`

## 역할

- 목적: DB 정렬 순서 열거형을 제공한다.
- 설명: 오름차순/내림차순 정렬 옵션을 정의한다.
- 디자인 패턴: 열거형

## 주요 구성

- 클래스: `SortOrder`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/models.py`
