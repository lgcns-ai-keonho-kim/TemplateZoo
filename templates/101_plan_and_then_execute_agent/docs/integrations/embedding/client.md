# Client 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/embedding/client.py`

## 역할

- 목적: LangChain Embeddings 기반 임베딩 클라이언트를 제공한다.
- 설명: 임베딩 호출을 래핑해 로깅과 예외 처리를 통합한다.
- 디자인 패턴: 프록시, 데코레이터

## 주요 구성

- 클래스: `EmbeddingClient`
- 함수: 없음

## 실패 경로

- `EMBEDDING_DIMENSION_INCONSISTENT`
- `EMBEDDING_DOCUMENT_COUNT_MISMATCH`
- `EMBEDDING_VECTOR_EMPTY`
- `EMBEDDING_VECTOR_INVALID`

## 연관 코드

- `src/plan_and_then_execute_agent/shared/logging`
- `src/plan_and_then_execute_agent/shared/exceptions`
