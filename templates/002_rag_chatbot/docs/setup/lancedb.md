# LanceDB 설정 가이드

이 문서는 현재 로컬 기본 벡터 저장소인 LanceDB의 사용 지점과 운영 포인트를 설명한다.

## 1. 현재 사용 경로

- ingestion backend: `--backend lancedb`
- online retrieval: `src/rag_chatbot/core/chat/nodes/rag_retrieve_node.py`
- 기본 경로: `LANCEDB_URI=data/db/vector`

## 2. 현재 구조

- 엔진 구현: `src/rag_chatbot/integrations/db/engines/lancedb/*`
- 적재 경로: `ingestion/steps/upsert_lancedb_step.py`
- 조회 경로: `rag_retrieve_node.py`

## 3. 유지보수/추가개발 포인트

- 적재 스키마와 조회 시 사용하는 컬렉션(`rag_chunks`) 규칙을 같이 유지해야 한다.
- 필터나 메타데이터 필드를 바꾸면 document mapper, filter engine, `rag_format_node` reference 구성까지 함께 점검해야 한다.
- 차원 변경은 기존 저장소와 바로 호환되지 않으므로 재적재 전략을 먼저 확정하는 편이 좋다.

## 4. 관련 문서

- `docs/setup/ingestion.md`
- `docs/integrations/db/engines/lancedb/engine.md`
- `docs/core/chat.md`
