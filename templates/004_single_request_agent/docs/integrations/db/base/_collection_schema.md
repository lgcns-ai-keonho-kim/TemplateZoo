# Collection Schema

## 개요

`src/single_request_agent/integrations/db/base/_collection_schema.py` 구현을 기준으로 현재 동작을 정리한다.

- DB 컬렉션 스키마 모델을 제공한다.
- 컬럼/페이로드/벡터 정책과 입력 검증 로직을 포함한 스키마 DTO를 정의한다.
- 구현 형태: 데이터 전송 객체(DTO)

## 주요 구성

- 클래스: `CollectionSchema`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_agent/integrations/db/base/models.py`
