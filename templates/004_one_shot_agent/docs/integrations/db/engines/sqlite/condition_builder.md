# Condition Builder

## 개요

`src/one_shot_agent/integrations/db/engines/sqlite/condition_builder.py` 구현을 기준으로 현재 동작을 정리한다.

- SQLite 조건 빌더 모듈을 제공한다.
- 필터 모델을 SQLite WHERE 절로 변환하고 메모리 필터 평가를 수행한다.
- 구현 형태: 빌더 패턴

## 주요 구성

- 클래스: `SqliteConditionBuilder`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/one_shot_agent/integrations/db/base/models.py`
