# Column Spec 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/base/_column_spec.py`

## 역할

- 목적: DB 컬럼 스펙 모델을 제공한다.
- 설명: 컬럼 이름/타입/벡터 속성 등 스키마 필드를 표현한다.
- 디자인 패턴: 데이터 전송 객체(DTO)

## 주요 구성

- 클래스: `ColumnSpec`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/models.py`
