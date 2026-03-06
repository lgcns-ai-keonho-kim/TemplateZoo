# engine 모듈

이 문서는 `src/rag_chatbot/integrations/db/engines/postgres/engine.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

PostgreSQL 기반 DB 엔진을 제공한다.

## 2. 설명

컬렉션 스키마 기반 CRUD와 PGVector 벡터 검색을 처리한다.

## 3. 디자인 패턴

어댑터 패턴

## 4. 주요 구성

- 클래스 `PostgresEngine`
  주요 메서드: `name`, `supports_vector_search`, `connect`, `close`, `create_collection`, `delete_collection`, `add_column`, `drop_column`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/base/engine.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
