# Sort Field

## 개요

`src/single_request_tool_agent/integrations/db/base/_sort_field.py` 구현을 기준으로 현재 동작을 정리한다.

- DB 정렬 필드 모델을 제공한다.
- 정렬 대상 필드와 출처/정렬 방향을 표현하는 DTO를 정의한다.
- 구현 형태: 데이터 전송 객체(DTO)

## 주요 구성

- 클래스: `SortField`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_tool_agent/integrations/db/base/models.py`
