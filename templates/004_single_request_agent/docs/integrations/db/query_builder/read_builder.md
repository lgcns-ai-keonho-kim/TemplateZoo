# Read Builder

## 개요

`src/single_request_agent/integrations/db/query_builder/read_builder.py` 구현을 기준으로 현재 동작을 정리한다.

- 읽기 전용 DSL 빌더를 제공한다.
- QueryBuilder를 감싸 체이닝 후 fetch()로 조회한다.
- 구현 형태: 빌더 패턴

## 주요 구성

- 클래스: `ReadBuilder`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_agent/integrations/db/base/query_builder.py`
