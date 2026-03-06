# schema_manager 모듈

이 문서는 `src/rag_chatbot/integrations/db/engines/postgres/schema_manager.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

PostgreSQL 스키마 관리 모듈을 제공한다.

## 2. 설명

테이블 생성/삭제와 컬럼 추가/삭제를 담당한다.

## 3. 디자인 패턴

매니저 패턴

## 4. 주요 구성

- 클래스 `PostgresSchemaManager`
  주요 메서드: `create_collection`, `delete_collection`, `add_column`, `drop_column`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/engines/postgres/vector_store.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
