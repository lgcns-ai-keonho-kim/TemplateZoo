# client 모듈

이 문서는 `src/rag_chatbot/integrations/embedding/client.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

LangChain Embeddings 기반 임베딩 클라이언트를 제공한다.

## 2. 설명

임베딩 호출을 래핑해 로깅과 예외 처리를 통합한다.

## 3. 디자인 패턴

프록시, 데코레이터

## 4. 주요 구성

- 클래스 `EmbeddingClient`
  주요 메서드: `embed_query`, `embed_documents`, `aembed_query`, `aembed_documents`

## 5. 연동 포인트

- `src/rag_chatbot/shared/logging`
- `src/rag_chatbot/shared/exceptions`

## 6. 관련 문서

- `docs/integrations/embedding/README.md`
- `docs/integrations/overview.md`
