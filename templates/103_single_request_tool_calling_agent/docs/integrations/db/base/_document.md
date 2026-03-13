# Document

## 개요

`src/single_request_tool_agent/integrations/db/base/_document.py` 구현을 기준으로 현재 동작을 정리한다.

- DB 문서 모델을 제공한다.
- 문서 ID/필드/페이로드/벡터를 담는 DTO를 정의한다.
- 구현 형태: 데이터 전송 객체(DTO)

## 주요 구성

- 클래스: `Document`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_tool_agent/integrations/db/base/models.py`
