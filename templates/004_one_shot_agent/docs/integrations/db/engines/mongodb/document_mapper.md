# Document Mapper

## 개요

`src/one_shot_agent/integrations/db/engines/mongodb/document_mapper.py` 구현을 기준으로 현재 동작을 정리한다.

- MongoDB 문서 매퍼 모듈을 제공한다.
- Document 모델과 MongoDB 레코드 간 변환을 담당한다.
- 구현 형태: 매퍼 패턴

## 주요 구성

- 클래스: `MongoDocumentMapper`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/one_shot_agent/integrations/db/base/models.py`
