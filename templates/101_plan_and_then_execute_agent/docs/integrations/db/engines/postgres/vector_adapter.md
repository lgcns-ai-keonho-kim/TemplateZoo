# Vector Adapter 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/engines/postgres/vector_adapter.py`

## 역할

- 목적: PGVector 타입 어댑터를 제공한다.
- 설명: pgvector 타입 등록, 파라미터 생성, 결과 파싱을 통합한다.
- 디자인 패턴: 어댑터 패턴

## 주요 구성

- 클래스: `PostgresVectorAdapter`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/engines/postgres/engine.py`
