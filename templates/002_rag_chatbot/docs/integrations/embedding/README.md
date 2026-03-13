# Integrations Embedding 가이드

이 문서는 `EmbeddingClient`와 임베딩 호출이 현재 어떻게 쓰이는지 설명한다.

## 1. 현재 역할

- 동기/비동기 임베딩 호출을 단일 래퍼로 노출한다.
- ingestion와 online retrieval가 같은 임베딩 계층을 공유한다.

## 2. 현재 사용 경로

- `ingestion/core/runner.py`: 문서 적재용 임베딩 생성
- `core/chat/nodes/rag_retrieve_node.py`: 사용자 질의 임베딩 생성

## 3. 유지보수/추가개발 포인트

- 임베딩 모델 또는 차원이 바뀌면 저장소 재적재 여부를 먼저 결정해야 한다.
- online query와 ingestion가 같은 모델/차원을 사용하도록 유지하는 편이 검색 품질을 지키기 쉽다.

## 4. 관련 문서

- `docs/integrations/embedding/client.md`
- `docs/setup/ingestion.md`
- `docs/setup/env.md`
