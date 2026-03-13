# Collection Info

## 개요

`src/single_request_agent/integrations/db/base/_collection_info.py` 구현을 기준으로 현재 동작을 정리한다.

- DB 컬렉션 정보 호환 모델을 제공한다.
- 기존 호환을 위해 CollectionSchema 별칭 클래스를 유지한다.
- 구현 형태: 별칭 래퍼

## 주요 구성

- 클래스: `CollectionInfo`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_agent/integrations/db/base/models.py`
