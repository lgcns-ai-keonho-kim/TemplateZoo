# Delete Builder

## 개요

`src/single_request_tool_agent/integrations/db/query_builder/delete_builder.py` 구현을 기준으로 현재 동작을 정리한다.

- 삭제 전용 DSL 빌더를 제공한다.
- ID 삭제와 QueryBuilder 기반 다건 삭제를 지원한다.
- 구현 형태: 파사드

## 주요 구성

- 클래스: `DeleteBuilder`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_tool_agent/integrations/db/base/query_builder.py`
