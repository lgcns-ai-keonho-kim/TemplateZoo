# Read Builder 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/query_builder/read_builder.py`

## 역할

- 목적: 읽기 전용 DSL 빌더를 제공한다.
- 설명: QueryBuilder를 감싸 체이닝 후 fetch()로 조회한다.
- 디자인 패턴: 빌더 패턴

## 주요 구성

- 클래스: `ReadBuilder`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/query_builder.py`
