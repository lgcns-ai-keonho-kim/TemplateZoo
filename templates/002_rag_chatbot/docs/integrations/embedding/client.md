# EmbeddingClient

## 역할

- LangChain `Embeddings` 래퍼다.
- 동기/비동기 임베딩 호출에 로깅, 출력 검증, 예외 표준화를 추가한다.
- ingestion와 online retrieval가 같은 래퍼 계층을 사용한다.

## 공개 메서드

- `embed_query`
- `embed_documents`
- `aembed_query`
- `aembed_documents`

## 검증

- 문서 개수와 결과 벡터 개수가 다르면 `EMBEDDING_DOCUMENT_COUNT_MISMATCH`
- 벡터 차원이 비어 있거나 형식이 잘못되면 `EMBEDDING_VECTOR_EMPTY`, `EMBEDDING_VECTOR_INVALID`
- 문서 벡터 차원이 서로 다르면 `EMBEDDING_DIMENSION_INCONSISTENT`

## 로깅

- `Logger`, `LogRepository`, `BaseDBEngine` 중 하나를 받아 로그 경로를 구성할 수 있다.
- `log_payload`, `log_response`로 입력과 결과 기록 여부를 제어한다.
- 성공 로그에는 입력 개수, 입력 문자 수, 출력 개수, 차원이 포함된다.
