# Integrations Embedding 가이드

이 문서는 `src/rag_chatbot/integrations/embedding/client.py`의 `EmbeddingClient` 인터페이스와 동작 규칙을 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| Embeddings | LangChain 임베딩 베이스 타입 | `langchain_core.embeddings` |
| EmbeddingClient | 임베딩 호출/로깅/예외를 표준화한 래퍼 | `integrations/embedding/client.py` |
| logging_engine | 로깅 주입 대상(엔진/로거/저장소) | `EmbeddingClient.__init__` |
| EmbeddingLogRepository | 임베딩 로그 전용 DB 저장소 | `shared/logging/embedding_repository.py` |

## 2. 관련 스크립트

| 파일 | 역할 |
| --- | --- |
| `src/rag_chatbot/integrations/embedding/client.py` | EmbeddingClient 구현 |
| `src/rag_chatbot/integrations/embedding/__init__.py` | 공개 API 제공 |
| `src/rag_chatbot/shared/logging/embedding_repository.py` | 임베딩 로그 DB 저장소 |
| `ingestion/core/enrichment.py` | 비동기 문서 임베딩 배치 실행 |
| `ingestion/core/runner.py` | ingestion 임베더 생성 |
| `src/rag_chatbot/core/chat/nodes/rag_retrieve_node.py` | RAG 검색 임베더 생성 |

## 3. 인터페이스

호출 메서드:

1. 동기 질의: `embed_query(text)`
2. 동기 문서: `embed_documents(texts)`
3. 비동기 질의: `aembed_query(text)`
4. 비동기 문서: `aembed_documents(texts)`

동작 규칙:

1. 내부 모델이 반환한 벡터를 `float` 리스트로 정규화한다.
2. 문서 결과 개수와 입력 개수가 다르면 예외를 발생시킨다.
3. 벡터가 비어 있거나 차원이 문서별로 다르면 예외를 발생시킨다.

## 4. 로깅 주입 규칙

`logging_engine` 허용 타입:

1. `BaseDBEngine`
2. `Logger`
3. `LogRepository`

동작:

1. `BaseDBEngine` 주입 시 내부에서 `DBClient(engine)`를 만들고 `EmbeddingLogRepository`를 자동 구성한다.
2. `logger`가 있으면 그대로 사용한다.
3. `log_repository`만 있으면 `InMemoryLogger`를 생성한다.
4. 둘 다 없으면 `create_default_logger(name)`를 사용한다.

## 5. 로그 메타데이터

기본 메타 키:

1. `action`
2. `model_name`
3. `provider`
4. `client_name`

시작 시 추가:

1. `input_count`
2. `input_chars`
3. `payload` (`log_payload=True`일 때)

성공 시 추가:

1. `duration_ms`
2. `success`
3. `output_count`
4. `dimension`
5. `response` (`log_response=True`일 때)

실패 시 추가:

1. `duration_ms`
2. `success=False`
3. `error_type`

## 6. 예외 코드

### 6-1. EmbeddingClient

| 상황 | 코드 |
| --- | --- |
| 동기 질의 실패 | `EMBED_QUERY_ERROR` |
| 동기 문서 실패 | `EMBED_DOCUMENTS_ERROR` |
| 비동기 질의 실패 | `EMBED_AQUERY_ERROR` |
| 비동기 문서 실패 | `EMBED_ADOCUMENTS_ERROR` |
| 벡터 형식 오류 | `EMBEDDING_VECTOR_INVALID` |
| 빈 벡터 반환 | `EMBEDDING_VECTOR_EMPTY` |
| 문서 임베딩 개수 불일치 | `EMBEDDING_DOCUMENT_COUNT_MISMATCH` |
| 문서 임베딩 차원 불일치 | `EMBEDDING_DIMENSION_INCONSISTENT` |

### 6-2. ingestion 비동기 임베딩 단계

| 상황 | 코드 |
| --- | --- |
| 비동기 임베딩 실패 | `INGESTION_EMBEDDING_ASYNC_FAILED` |
| 임베딩 결과 개수 불일치 | `INGESTION_EMBEDDING_COUNT_MISMATCH` |
| 임베더 비동기 미지원 | `INGESTION_EMBEDDER_ASYNC_UNSUPPORTED` |
| 배치 결과 개수 불일치 | `INGESTION_EMBEDDING_BATCH_MISMATCH` |

## 7. 사용 예시

### 7-1. 기본 임베더 생성

```python
import os

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from rag_chatbot.integrations.embedding import EmbeddingClient
from rag_chatbot.shared.config import resolve_gemini_embedding_dim

dimension = resolve_gemini_embedding_dim()

embedder = EmbeddingClient(
    model=GoogleGenerativeAIEmbeddings(
        model=os.getenv("GEMINI_EMBEDDING_MODEL", ""),
        project=os.getenv("GEMINI_PROJECT", ""),
        output_dimensionality=dimension,
    ),
    name="example-embedding-client",
)

vector = embedder.embed_query("안녕하세요")
```

### 7-2. ingestion 비동기 문서 임베딩 경로

`ingestion/core/enrichment.py`는 `embedder.aembed_documents(...)`를 배치 호출한다.

1. 기본 배치 크기: `32`
2. 표 블록은 `<SUMMARY>`, `<DESCRIPTION>`를 우선 임베딩 소스로 사용
3. 문서 전체 개수와 결과 개수를 반드시 검증

## 8. 운영 체크리스트

1. `GEMINI_EMBEDDING_DIM`은 1 이상의 정수여야 한다.
2. ingestion과 RAG 검색 노드가 같은 `GEMINI_EMBEDDING_DIM`을 사용해야 한다.
3. 저장소 차원 불일치 시 `--reset` 재적재 절차를 운영 절차에 포함한다.
4. 대량 배치에서는 API 한도/지연 시간을 고려해 배치 크기를 조정한다.

## 9. 관련 문서

- `docs/integrations/overview.md`
- `docs/integrations/llm.md`
- `docs/setup/ingestion.md`
- `docs/setup/lancedb.md`
- `docs/setup/env.md`
