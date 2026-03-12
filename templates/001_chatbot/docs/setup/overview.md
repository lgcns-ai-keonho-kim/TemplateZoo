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
2. 로그 저장은 파일 시스템 저장소로 확장할 수 있다.
3. 환경별 설정은 `src/chatbot/resources/dev|stg|prod/.env`를 추가 로드하는 방식으로 분리할 수 있다.

## 3. 문서 읽기 순서

1. `docs/setup/env.md`
2. `docs/setup/sqlite.md`
3. 필요 시 `docs/setup/postgresql_pgvector.md`, `docs/setup/mongodb.md`, `docs/setup/lancedb.md`
4. 보조 저장소가 필요하면 `docs/setup/filesystem.md`
5. 장애 시 `docs/setup/troubleshooting.md`

## 4. 유지보수 포인트

1. setup 문서는 항상 현재 기본 런타임과 선택 확장 경로를 분리해 적어야 한다.
2. `.env.sample`에 남아 있는 실험/구버전 키와 현재 코드가 실제 소비하는 키를 혼동하지 않도록 설명해야 한다.
3. 인프라 예시를 추가하더라도 `runtime.py` 조립이 바뀌지 않았다면 기본 동작이 바뀐 것처럼 서술하면 안 된다.

## 5. 관련 문서

- `docs/setup/env.md`
- `docs/setup/sqlite.md`
- `docs/setup/lancedb.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/setup/mongodb.md`
- `docs/setup/filesystem.md`
- `docs/setup/troubleshooting.md`
