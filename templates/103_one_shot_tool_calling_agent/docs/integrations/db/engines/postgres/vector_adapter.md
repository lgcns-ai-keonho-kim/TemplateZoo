# Vector Adapter

## 개요

`src/one_shot_tool_calling_agent/integrations/db/engines/postgres/vector_adapter.py` 구현을 기준으로 현재 동작을 정리한다.

- PGVector 타입 어댑터를 제공한다.
- pgvector 타입 등록, 파라미터 생성, 결과 파싱을 통합한다.
- 구현 형태: 어댑터 패턴

## 주요 구성

- 클래스: `PostgresVectorAdapter`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/one_shot_tool_calling_agent/integrations/db/engines/postgres/engine.py`
