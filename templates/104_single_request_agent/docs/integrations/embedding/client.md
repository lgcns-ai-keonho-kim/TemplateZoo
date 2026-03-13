# Client

## 개요

`src/single_request_agent/integrations/embedding/client.py` 구현을 기준으로 현재 동작을 정리한다.

- LangChain Embeddings 기반 임베딩 클라이언트를 제공한다.
- 임베딩 호출을 래핑해 로깅과 예외 처리를 통합한다.
- 구현 형태: 프록시, 데코레이터

## 주요 구성

- 클래스: `EmbeddingClient`
- 함수: 없음

## 실패 경로

- `EMBEDDING_DIMENSION_INCONSISTENT`
- `EMBEDDING_DOCUMENT_COUNT_MISMATCH`
- `EMBEDDING_VECTOR_EMPTY`
- `EMBEDDING_VECTOR_INVALID`

## 관련 코드

- `src/single_request_agent/shared/logging`
- `src/single_request_agent/shared/exceptions`
