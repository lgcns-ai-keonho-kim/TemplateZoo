# embedding/client.md

소스 경로: `src/text_to_sql/integrations/embedding/client.py`

## 1. 역할

- LangChain Embeddings 기반 임베딩 클라이언트를 제공한다.
- 임베딩 호출을 래핑해 로깅과 예외 처리를 통합한다.
- 내부 구조는 프록시, 데코레이터 기반이다.

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `EmbeddingClient` | `__init__, embed_query, embed_documents, aembed_query, aembed_documents` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- `EMBEDDING_DIMENSION_INCONSISTENT`
- `EMBEDDING_DOCUMENT_COUNT_MISMATCH`
- `EMBEDDING_VECTOR_EMPTY`
- `EMBEDDING_VECTOR_INVALID`

## 4. 관련 코드

- `src/text_to_sql/shared/logging`
- `src/text_to_sql/shared/exceptions`
- `src/text_to_sql/shared/exceptions/__init__.py`
- `src/text_to_sql/shared/logging/__init__.py`
