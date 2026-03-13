# Setup 레퍼런스 개요

이 문서는 현재 코드 기준 기본 실행 경로와 선택 확장 경로를 구분해 `docs/setup` 문서를 안내한다.

## 1. 기본 런타임

| 항목 | 현재 기본값 | 코드 기준 |
| --- | --- | --- |
| 환경 로딩 | 루트 `.env` + 선택적 `resources/<env>/.env` | `RuntimeEnvironmentLoader` |
| LLM | Gemini 노드 조립 | `core/chat/nodes/*.py` |
| 채팅 이력 저장소 | SQLite | `ChatHistoryRepository` 기본 생성자 |
| 작업 큐 | InMemoryQueue | `api/chat/services/runtime.py` |
| 이벤트 버퍼 | InMemoryEventBuffer | `api/chat/services/runtime.py` |
| 정적 UI | `/ui` 마운트 | `api/main.py` |

## 2. 선택 확장 경로

1. DB 저장소를 PostgreSQL, MongoDB, Redis, Elasticsearch, LanceDB로 확장할 수 있다.
2. 로그 저장을 파일 시스템 저장소로 확장할 수 있다.
3. `dev`, `stg`, `prod` 환경은 `src/chatbot/resources/<env>/.env`를 추가 로드하는 방식으로 분리한다.

## 3. 먼저 읽을 문서

1. `docs/setup/env.md`
2. `docs/setup/sqlite.md`
3. 필요 시 `docs/setup/postgresql_pgvector.md`, `docs/setup/mongodb.md`, `docs/setup/lancedb.md`
4. 파일 로그 저장이 필요하면 `docs/setup/filesystem.md`
5. 장애 대응은 `docs/setup/troubleshooting.md`

## 4. 유지보수 포인트

1. setup 문서는 항상 현재 기본 런타임과 선택 확장 경로를 분리해서 적어야 한다.
2. `.env.sample`에 남아 있는 보관용 키와 실제 코드가 읽는 키를 혼동하지 않아야 한다.
3. 조립 코드가 바뀌지 않았다면 문서상 기본 동작도 바뀌지 않는다.
