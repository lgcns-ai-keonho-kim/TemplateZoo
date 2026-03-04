# Integrations 모듈 가이드

이 문서는 `src/rag_chatbot/integrations` 계층의 책임, 구성 요소, 교체 절차를 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| 통합 계층 | 외부 시스템(DB, LLM, 임베딩, 파일시스템)과 직접 통신하는 계층 | `src/rag_chatbot/integrations/*` |
| DB 엔진 | 저장소별 CRUD/검색 구현체 | `integrations/db/engines/*/engine.py` |
| DB 클라이언트 | 엔진 공통 호출 퍼사드 | `integrations/db/client.py` |
| LLM 클라이언트 | 모델 호출/로깅/예외 표준화 래퍼 | `integrations/llm/client.py` |
| 임베딩 클라이언트 | 임베딩 호출/로깅/예외 표준화 래퍼 | `integrations/embedding/client.py` |
| 파일 시스템 엔진 | 파일 읽기/쓰기/목록/이동/복사 인터페이스 | `integrations/fs/base/engine.py` |

## 2. 모듈 구성

| 경로 | 책임 | 주요 스크립트 |
| --- | --- | --- |
| `src/rag_chatbot/integrations/db` | DB 엔진 추상화, Query DSL, 엔진별 구현 | `client.py`, `base/*.py`, `query_builder/*.py`, `engines/*` |
| `src/rag_chatbot/integrations/llm` | LangChain 채팅 모델 래핑 + 로깅/예외 | `client.py` |
| `src/rag_chatbot/integrations/embedding` | LangChain 임베딩 래핑 + 로깅/예외 | `client.py` |
| `src/rag_chatbot/integrations/fs` | 파일 시스템 추상화 + 파일 로그 저장소 | `base/engine.py`, `engines/local.py`, `file_repository.py` |

## 3. 책임 경계

1. API 라우터는 integrations 구현체를 직접 생성하지 않는다.
2. 조립은 `api/chat/services/runtime.py` 또는 ingestion runner에서 수행한다.
3. 상위 계층은 가능하면 퍼사드(`DBClient`, `LLMClient`, `EmbeddingClient`)에만 의존한다.

## 4. 교체 전략

### 4-1. DB 엔진 교체

1. 엔진 인스턴스를 새 구현으로 교체
2. `DBClient(new_engine)` 생성
3. `ChatHistoryRepository(db_client=...)` 또는 ingestion upsert 경로에 주입

### 4-2. LLM 공급자 교체

1. 노드 조립 파일(`core/chat/nodes/*.py`)의 `BaseChatModel` 생성부 교체
2. `LLMClient` 래퍼 유지
3. 예외 코드와 로그 메타데이터 스키마 유지

### 4-3. 임베딩 공급자 교체

1. ingestion runner와 `rag_retrieve_node` 임베더 생성부 교체
2. `EmbeddingClient` 래퍼 유지
3. `GEMINI_EMBEDDING_DIM`과 저장소 벡터 차원 일치 확인
4. ingestion는 비동기 문서 임베딩(`aembed_documents`) 경로를 사용함을 전제로 검증

### 4-4. 파일 저장소 교체

1. `BaseFSEngine` 구현체 추가
2. `FileLogRepository(engine=...)` 주입
3. 호출 계층은 변경하지 않음

## 5. 소스 매칭 점검 항목

1. 문서에 기재한 경로가 실제 파일과 일치하는가
2. 공개 API 목록이 각 `__init__.py` 노출 항목과 일치하는가
3. 교체 절차가 실제 조립 지점과 일치하는가

## 6. 관련 문서

- `docs/integrations/db.md`
- `docs/integrations/llm.md`
- `docs/integrations/embedding.md`
- `docs/integrations/fs.md`
- `docs/setup/ingestion.md`
- `docs/setup/lancedb.md`
