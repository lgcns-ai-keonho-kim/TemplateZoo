# Integrations 모듈 개요

이 문서는 `src/rag_chatbot/integrations` 전체 구조와 하위 문서 진입점을 제공한다.

## 1. 모듈 구조

```text
src/rag_chatbot/integrations/
  db/
    base/
    query_builder/
    engines/{sqlite,postgres,lancedb,redis,mongodb,elasticsearch}/
  llm/
  embedding/
  fs/
```

## 2. 책임 경계

1. integrations 계층은 외부 시스템 연동 구현을 담당한다.
2. 상위 계층은 `DBClient`, `LLMClient`, `EmbeddingClient`, `FileLogRepository` 같은 퍼사드/클라이언트 경계를 통해 연동한다.
3. 엔진 교체는 runtime 조립 계층에서 수행하고 상위 비즈니스 로직은 유지한다.

## 3. 문서 인덱스

- DB: `docs/integrations/db/README.md`
- LLM: `docs/integrations/llm/README.md`
- Embedding: `docs/integrations/embedding/README.md`
- FS: `docs/integrations/fs/README.md`

## 4. 교체 시 확인 항목

1. DB 엔진: 벡터 검색 지원 여부와 스키마 제약을 먼저 확인한다.
2. LLM/Embedding: 모델 제공자 변경 시 로깅/예외 코드 호환성을 유지한다.
3. FS 엔진: 경로 규칙과 손상 레코드 처리 정책을 기존 저장소와 맞춘다.

## 5. 관련 문서

- `docs/setup/overview.md`
- `docs/setup/ingestion.md`
- `docs/shared/overview.md`
