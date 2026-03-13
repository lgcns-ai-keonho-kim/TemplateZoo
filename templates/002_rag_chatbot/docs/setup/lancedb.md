# LanceDB

## 현재 사용 경로

- ingestion backend: `--backend lancedb`
- online retrieval: `src/rag_chatbot/core/chat/nodes/rag_retrieve_node.py`
- 기본 경로: `LANCEDB_URI=data/db/vector`

## 관련 코드

- 엔진: `src/rag_chatbot/integrations/db/engines/lancedb/*`
- 적재: `ingestion/steps/upsert_lancedb_step.py`
- 컬렉션 이름: `rag_chunks`

## 유지 포인트

- 적재 스키마와 조회 스키마는 같이 유지해야 한다.
- reference 포맷을 바꾸면 `rag_format_node`와 UI reference 렌더링까지 함께 확인해야 한다.
- 차원 변경 시 기존 저장소와 바로 호환되지 않을 수 있다.
