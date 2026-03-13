# Document Mapper

## 개요

`src/single_request_tool_agent/integrations/db/engines/redis/document_mapper.py` 구현을 기준으로 현재 동작을 정리한다.

- Redis 문서 매퍼 모듈을 제공한다.
- Document 모델과 Redis Hash 데이터 간 변환을 담당한다.
- 구현 형태: 매퍼 패턴

## 주요 구성

- 클래스: `RedisDocumentMapper`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_tool_agent/integrations/db/base/models.py`
