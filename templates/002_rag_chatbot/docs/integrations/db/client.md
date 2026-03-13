# DBClient 가이드

이 문서는 `src/rag_chatbot/integrations/db/client.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

DBClient는 엔진, 스키마 캐시, DSL 빌더를 묶는 퍼사드다.

## 2. 공개 구성

- 클래스 `DBClient`
  공개 메서드: `engine`, `connect`, `close`, `register_schema`, `get_schema`, `create_collection`, `delete_collection`, `add_column`, `drop_column`, `write`, `read`, `delete`, `fetch`, `upsert`, `vector_search`

## 3. 코드 설명

- 스키마는 내부 캐시에 deep copy로 보관하며, 엔진 capability와 맞지 않는 벡터 필드 등록을 막는다.
- 읽기/쓰기/삭제는 각각 별도 DSL 빌더로 분리된다.
- SQLite 엔진일 때는 읽기 I/O도 직렬화해 잠금 충돌을 줄인다.

## 4. 유지보수/추가개발 포인트

- 스키마 검증 오류 메시지는 상위 계층 디버깅에 직접 보이므로, 예외 원인을 분명히 유지하는 편이 낫다.
- 새 엔진을 붙일 때는 `supports_vector_search`와 차원 검증 규칙이 기존 엔진과 같은 의미를 갖는지 먼저 맞춰야 한다.

## 5. 관련 문서

- `docs/integrations/overview.md`
- `docs/integrations/db/README.md`
