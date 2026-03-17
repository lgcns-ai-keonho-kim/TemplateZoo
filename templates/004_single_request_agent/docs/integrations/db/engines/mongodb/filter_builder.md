# Filter Builder

## 개요

`src/single_request_agent/integrations/db/engines/mongodb/filter_builder.py` 구현을 기준으로 현재 동작을 정리한다.

- MongoDB 필터 쿼리 빌더를 제공한다.
- 필터 조건을 MongoDB 쿼리로 변환한다.
- 구현 형태: 빌더 패턴

## 주요 구성

- 클래스: `MongoFilterBuilder`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_agent/integrations/db/engines/mongodb/engine.py`
