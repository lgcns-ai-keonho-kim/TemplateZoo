# Schema Manager

## 개요

`src/single_request_tool_agent/integrations/db/engines/mongodb/schema_manager.py` 구현을 기준으로 현재 동작을 정리한다.

- MongoDB 스키마 관리 모듈을 제공한다.
- 컬렉션 생성/삭제 및 필드 제거 동작을 담당한다.
- 구현 형태: 매니저 패턴

## 주요 구성

- 클래스: `MongoSchemaManager`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_tool_agent/integrations/db/engines/mongodb/engine.py`
