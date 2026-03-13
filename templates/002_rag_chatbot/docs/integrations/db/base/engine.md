# BaseDBEngine 가이드

이 문서는 `src/rag_chatbot/integrations/db/base/engine.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

DB 엔진 구현체가 따라야 하는 공통 포트를 정의한다. 컬렉션 관리, 일반 조회, 벡터 검색 계약이 여기서 고정된다.

## 2. 공개 구성

- 클래스 `BaseDBEngine`
  공개 메서드: `name`, `supports_vector_search`, `connect`, `close`, `create_collection`, `delete_collection`, `add_column`, `drop_column`, `upsert`, `get`, `delete`, `query`, `vector_search`

## 3. 코드 설명

- 모든 엔진 구현체는 컬렉션 관리, CRUD, 벡터 검색 메서드를 같은 시그니처로 구현해야 한다.

## 4. 유지보수/추가개발 포인트

- 이 모듈을 확장할 때는 같은 계층의 이웃 모듈과 계약이 어디에서 맞물리는지 먼저 확인하는 편이 안전하다.

## 5. 관련 문서

- `docs/integrations/overview.md`
- `docs/integrations/db/README.md`
