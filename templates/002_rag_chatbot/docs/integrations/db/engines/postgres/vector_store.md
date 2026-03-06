# vector_store 모듈

이 문서는 `src/rag_chatbot/integrations/db/engines/postgres/vector_store.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

PostgreSQL 벡터 관리 모듈을 제공한다.

## 2. 설명

PGVector 확장/인덱스 생성과 벡터 컬럼 유효성 판단을 담당한다.

## 3. 디자인 패턴

매니저 패턴

## 4. 주요 구성

- 클래스 `PostgresVectorStore`
  주요 메서드: `adapter`, `has_vector_column`, `ensure_vector_extension`, `ensure_vector_index`, `drop_vector_index_if_needed`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/engines/postgres/vector_adapter.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
