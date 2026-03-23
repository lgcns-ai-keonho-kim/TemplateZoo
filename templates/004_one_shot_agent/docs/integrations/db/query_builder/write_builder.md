# Write Builder

## 개요

`src/one_shot_agent/integrations/db/query_builder/write_builder.py` 구현을 기준으로 현재 동작을 정리한다.

- 쓰기 전용 DSL 빌더를 제공한다.
- 업서트 중심의 간단한 쓰기 호출을 제공한다.
- 구현 형태: 파사드

## 주요 구성

- 클래스: `WriteBuilder`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/one_shot_agent/integrations/db/base/engine.py`
