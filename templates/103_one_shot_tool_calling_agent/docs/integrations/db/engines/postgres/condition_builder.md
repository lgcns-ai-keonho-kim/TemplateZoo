# Condition Builder

## 개요

`src/one_shot_tool_calling_agent/integrations/db/engines/postgres/condition_builder.py` 구현을 기준으로 현재 동작을 정리한다.

- PostgreSQL 조건 빌더 모듈을 제공한다.
- 필터 모델을 PostgreSQL WHERE 절로 변환한다.
- 구현 형태: 빌더 패턴

## 주요 구성

- 클래스: `PostgresConditionBuilder`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/one_shot_tool_calling_agent/integrations/db/base/models.py`
