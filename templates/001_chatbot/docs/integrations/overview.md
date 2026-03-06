# Integrations 모듈 레퍼런스

`src/chatbot/integrations` 계층을 폴더 구조 기준으로 탐색하기 위한 인덱스다.

## 1. 디렉터리 매핑

| 코드 경로 | 문서 |
| --- | --- |
| `src/chatbot/integrations` | `docs/integrations/overview.md` |
| `src/chatbot/integrations/db` | `docs/integrations/db/overview.md` |
| `src/chatbot/integrations/llm` | `docs/integrations/llm/overview.md` |
| `src/chatbot/integrations/fs` | `docs/integrations/fs/overview.md` |

## 2. 패키지 공개 API (`__init__.py`)

`src/chatbot/integrations/__init__.py` 공개 항목:

1. DB: `DBClient`, `ReadBuilder`, `WriteBuilder`, `DeleteBuilder`
2. DB 엔진: `LanceDBEngine`, `SQLiteEngine`, `RedisEngine`, `ElasticsearchEngine`, `MongoDBEngine`, `PostgresEngine`
3. LLM: `LLMClient`

## 3. 하위 문서 진입점

1. DB 상세: `docs/integrations/db/overview.md`
2. LLM 상세: `docs/integrations/llm/overview.md`
3. FS 상세: `docs/integrations/fs/overview.md`

## 4. 운영에서 먼저 보는 문서

1. DB 엔진 교체/장애 대응: `docs/integrations/db/overview.md`
2. 모델 호출/로깅 이슈: `docs/integrations/llm/client.md`
3. 파일 로그 저장 이슈: `docs/integrations/fs/file_repository.md`

## 5. 관련 문서

- `docs/setup/sqlite.md`
- `docs/setup/lancedb.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/setup/mongodb.md`
- `docs/setup/filesystem.md`
- `docs/shared/chat/overview.md`
