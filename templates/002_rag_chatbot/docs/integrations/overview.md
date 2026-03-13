# Integrations

## 구성

- `integrations/db`: 엔진 포트, 스키마 모델, query builder, 백엔드 구현체
- `integrations/llm`: LangChain `BaseChatModel` 래퍼
- `integrations/embedding`: LangChain `Embeddings` 래퍼
- `integrations/fs`: 파일 시스템 엔진과 파일 로그 저장소

## 현재 활성 경로

- Chat 기본 저장소: SQLite 경로의 `ChatHistoryRepository`
- online retrieval 기본 경로: LanceDB
- ingestion backend: LanceDB, PostgreSQL, Elasticsearch

## 기본 경로가 아닌 구현

- MongoDB, Redis, PostgreSQL Chat 저장소 전환은 구현은 있지만 기본 런타임 조립 대상이 아니다.
- 파일 로그 저장소는 구현돼 있지만 기본 런타임에 자동 주입되지 않는다.
