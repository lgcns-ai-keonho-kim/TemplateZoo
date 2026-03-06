# Field Source 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/base/_field_source.py`

## 역할

- 목적: DB 필드 출처 열거형을 제공한다.
- 설명: 필드가 컬럼/페이로드 중 어디에서 조회되는지 표현한다.
- 디자인 패턴: 열거형

## 주요 구성

- 클래스: `FieldSource`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/models.py`
