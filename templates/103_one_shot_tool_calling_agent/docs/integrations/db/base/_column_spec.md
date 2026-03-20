# Column Spec

## 개요

`src/one_shot_tool_calling_agent/integrations/db/base/_column_spec.py` 구현을 기준으로 현재 동작을 정리한다.

- DB 컬럼 스펙 모델을 제공한다.
- 컬럼 이름/타입/벡터 속성 등 스키마 필드를 표현한다.
- 구현 형태: 데이터 전송 객체(DTO)

## 주요 구성

- 클래스: `ColumnSpec`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/one_shot_tool_calling_agent/integrations/db/base/models.py`
