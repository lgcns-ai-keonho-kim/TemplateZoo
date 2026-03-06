# Condition Builder 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/engines/postgres/condition_builder.py`

## 역할

- 목적: PostgreSQL 조건 빌더 모듈을 제공한다.
- 설명: 필터 모델을 PostgreSQL WHERE 절로 변환한다.
- 디자인 패턴: 빌더 패턴

## 주요 구성

- 클래스: `PostgresConditionBuilder`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/models.py`
