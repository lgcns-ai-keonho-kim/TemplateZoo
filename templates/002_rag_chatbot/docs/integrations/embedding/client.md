# EmbeddingClient 가이드

이 문서는 `src/rag_chatbot/integrations/embedding/client.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

EmbeddingClient는 동기/비동기 임베딩 호출을 얇게 감싸 상위 계층이 구현체를 직접 알지 않도록 만든다.

## 2. 공개 구성

- 클래스 `EmbeddingClient`
  공개 메서드: `embed_query`, `embed_documents`, `aembed_query`, `aembed_documents`

## 3. 코드 설명

- 동기와 비동기 임베딩 메서드를 모두 노출해 ingestion와 online retrieval가 같은 래퍼를 사용한다.

## 4. 유지보수/추가개발 포인트

- 차원 변경은 ingestion 저장소와 online retrieval 모두에 영향을 주므로 재적재 전략을 같이 점검해야 한다.

## 5. 관련 문서

- `docs/integrations/overview.md`
