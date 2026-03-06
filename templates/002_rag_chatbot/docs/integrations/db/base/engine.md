# engine 모듈

이 문서는 `src/rag_chatbot/integrations/db/base/engine.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

DB 엔진 추상 인터페이스를 정의한다.

## 2. 설명

컬렉션 관리, 문서 CRUD, 벡터 검색을 위한 표준 메서드를 제공한다.

## 3. 디자인 패턴

전략 패턴

## 4. 주요 구성

- 클래스 `BaseDBEngine`
  주요 메서드: `name`, `supports_vector_search`, `connect`, `close`, `create_collection`, `delete_collection`, `add_column`, `drop_column`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/base/models.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
