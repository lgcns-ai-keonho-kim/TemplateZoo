# client 모듈

이 문서는 `src/rag_chatbot/integrations/db/client.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

공통 DB 클라이언트를 제공한다.

## 2. 설명

엔진을 주입받아 CRUD 중심의 단순한 호출을 제공한다.

## 3. 디자인 패턴

파사드

## 4. 주요 구성

- 클래스 `DBClient`
  주요 메서드: `engine`, `connect`, `close`, `register_schema`, `get_schema`, `create_collection`, `delete_collection`, `add_column`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/base/engine.py`
- `src/rag_chatbot/integrations/db/base/query_builder.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
