# Delete Builder 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/query_builder/delete_builder.py`

## 역할

- 목적: 삭제 전용 DSL 빌더를 제공한다.
- 설명: ID 삭제와 QueryBuilder 기반 다건 삭제를 지원한다.
- 디자인 패턴: 파사드

## 주요 구성

- 클래스: `DeleteBuilder`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/query_builder.py`
