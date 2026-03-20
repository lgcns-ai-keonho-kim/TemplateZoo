# Filter Operator

## 개요

`src/one_shot_tool_calling_agent/integrations/db/base/_filter_operator.py` 구현을 기준으로 현재 동작을 정리한다.

- DB 필터 연산자 열거형을 제공한다.
- 동등/범위/집합/포함 기반 비교 연산자를 정의한다.
- 구현 형태: 열거형

## 주요 구성

- 클래스: `FilterOperator`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/one_shot_tool_calling_agent/integrations/db/base/models.py`
