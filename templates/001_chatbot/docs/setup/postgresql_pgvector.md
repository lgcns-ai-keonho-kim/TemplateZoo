# PostgreSQL + pgvector 구성 레퍼런스

이 문서는 PostgreSQL 엔진과 pgvector 기반 확장을 현재 코드에 연결하는 지점을 설명한다.
현재 기본 채팅 런타임은 PostgreSQL을 자동으로 사용하지 않는다.

## 1. 현재 코드 기준 확장 경로

1. `src/chatbot/integrations/db/engines/postgres/*`가 엔진 구현을 제공한다.
2. `src/chatbot/api/chat/services/runtime.py`에는 `PostgresEngine`을 주입하는 예시 코드가 주석으로 남아 있다.
3. 실제 전환은 `ChatHistoryRepository(db_client=DBClient(PostgresEngine(...)))` 형태로 조립을 바꿀 때만 일어난다.

## 2. 필요한 환경 변수

```env
POSTGRES_DSN=
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PW=postgres
POSTGRES_DATABASE=playground
```

## 3. 유지보수 포인트

1. DSN 우선 정책과 개별 host/port/user 조합 정책을 문서와 코드에서 일치시켜야 한다.
2. pgvector 사용 여부는 단순 연결 문제가 아니라 스키마, 인덱스, 거리 계산 규칙과 연결된다.
3. 기본 런타임 문서에 PostgreSQL을 기본 저장소처럼 적으면 안 된다.

## 4. 추가 개발과 확장 시 주의점

1. 실제 전환 시에는 `runtime.py` 조립 변경, 초기 스키마 준비, 운영 마이그레이션 계획이 함께 필요하다.
2. PostgreSQL을 기본 이력 저장과 벡터 검색에 모두 쓰려면 일반 CRUD와 vector store 계약을 같이 검토해야 한다.

## 5. 관련 문서

- `docs/integrations/db/engines/postgres/engine.md`
- `docs/integrations/db/engines/postgres/vector_store.md`
- `docs/integrations/db/overview.md`
- `docs/setup/env.md`
