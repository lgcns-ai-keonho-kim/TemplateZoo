# MongoDBEngine 가이드

이 문서는 `src/rag_chatbot/integrations/db/engines/mongodb/engine.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

`mongodb` 백엔드용 `BaseDBEngine` 구현체다. 컬렉션 생성, CRUD, 필터 조회, 벡터 검색을 해당 드라이버 제약에 맞춰 수행한다.

## 2. 공개 구성

- 클래스 `MongoDBEngine`
  공개 메서드: `name`, `supports_vector_search`, `connect`, `close`, `create_collection`, `delete_collection`, `add_column`, `drop_column`, `upsert`, `get`, `delete`, `query`, `vector_search`

## 3. 코드 설명

- 상위 계층은 이 구현체를 직접 호출하지 않고 `DBClient`를 통해 접근하는 것이 기본 경로다.
- 엔진별 `supports_vector_search` 값이 스키마 등록과 벡터 검색 가능 여부를 결정한다.

## 4. 유지보수/추가개발 포인트

- 새 엔진 기능을 추가할 때는 `BaseDBEngine` 포트와 `DBClient` 검증 로직을 먼저 확인한다.
- 컬럼 추가/삭제, 벡터 검색 지원 여부, 필터 fallback 여부를 문서와 테스트에 함께 반영하는 편이 안전하다.

## 5. 관련 문서

- `docs/integrations/overview.md`
- `docs/integrations/db/README.md`
