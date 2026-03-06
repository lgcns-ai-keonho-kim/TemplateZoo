# vector_adapter 모듈

이 문서는 `src/rag_chatbot/integrations/db/engines/postgres/vector_adapter.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

PGVector 타입 어댑터를 제공한다.

## 2. 설명

pgvector 타입 등록, 파라미터 생성, 결과 파싱을 통합한다.

## 3. 디자인 패턴

어댑터 패턴

## 4. 주요 구성

- 클래스 `PostgresVectorAdapter`
  주요 메서드: `enabled`, `register`, `param`, `distance_expr`, `parse`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/engines/postgres/engine.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
