# Query Builder 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/base/query_builder.py`

## 역할

- 목적: 공통 DSL 기반 QueryBuilder를 제공한다.
- 설명: 체이닝 방식으로 Filter/Sort/Pagination을 구성해 Query 모델을 생성한다.
- 디자인 패턴: 빌더 패턴

## 주요 구성

- 클래스: `QueryBuilder`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/models.py`
