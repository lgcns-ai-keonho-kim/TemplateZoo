# Field Source

## 개요

`src/one_shot_tool_calling_agent/integrations/db/base/_field_source.py` 구현을 기준으로 현재 동작을 정리한다.

- DB 필드 출처 열거형을 제공한다.
- 필드가 컬럼/페이로드 중 어디에서 조회되는지 표현한다.
- 구현 형태: 열거형

## 주요 구성

- 클래스: `FieldSource`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/one_shot_tool_calling_agent/integrations/db/base/models.py`
