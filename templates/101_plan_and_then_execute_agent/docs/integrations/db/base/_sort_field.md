# Sort Field 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/base/_sort_field.py`

## 역할

- 목적: DB 정렬 필드 모델을 제공한다.
- 설명: 정렬 대상 필드와 출처/정렬 방향을 표현하는 DTO를 정의한다.
- 디자인 패턴: 데이터 전송 객체(DTO)

## 주요 구성

- 클래스: `SortField`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/models.py`
