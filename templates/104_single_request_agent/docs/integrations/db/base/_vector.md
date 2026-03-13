# Vector

## 개요

`src/single_request_agent/integrations/db/base/_vector.py` 구현을 기준으로 현재 동작을 정리한다.

- DB 벡터 모델을 제공한다.
- 벡터 값과 차원 정보를 표현하는 DTO를 정의한다.
- 구현 형태: 데이터 전송 객체(DTO)

## 주요 구성

- 클래스: `Vector`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_agent/integrations/db/base/models.py`
