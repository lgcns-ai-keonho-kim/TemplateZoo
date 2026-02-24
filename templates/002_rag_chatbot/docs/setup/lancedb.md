# LanceDB 구성 가이드

이 문서는 파일 기반 벡터 저장소를 LanceDB로 사용하는 절차를 정리한다.

## 1. 적용 범위

1. RAG 벡터 저장소를 로컬 파일 기반으로 운영할 때
2. PostgreSQL(pgvector), Elasticsearch가 아닌 경로로 벡터 검색을 수행할 때
3. SQLite는 RDB(세션/메시지 이력) 전용으로 유지할 때

## 2. 관련 코드

| 경로 | 역할 |
| --- | --- |
| `src/rag_chatbot/integrations/db/engines/lancedb/engine.py` | LanceDB CRUD/벡터 검색 엔진 |
| `src/rag_chatbot/core/chat/nodes/rag_retrieve_node.py` | RAG 검색 시 LanceDB 사용 |
| `ingestion/ingest_lancedb.py` | 문서 청킹/임베딩/LanceDB 적재 스크립트 |
| `ingestion/core/db.py` | LanceDB 클라이언트/스키마 빌더 |

## 3. 환경 변수

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `LANCEDB_URI` | `data/db/vector` | LanceDB 디렉터리 경로 |

예시:

```env
LANCEDB_URI=data/db/vector
```

## 4. ingestion 실행

```bash
uv run python ingestion/ingest_lancedb.py --input-root data/ingestion-doc
```

옵션:

1. `--chunk-workers`: 청킹 워커 수
2. `--sample`: 확장자별 1개 샘플만 처리

## 5. 동작 확인

1. `LANCEDB_URI` 경로에 `rag_chunks.lance`가 생성되는지 확인한다.
2. RAG 요청 시 `rag_retrieve_node`가 LanceDB에서 검색 결과를 반환하는지 확인한다.
3. SQLite(`CHAT_DB_PATH`)에는 채팅 이력만 저장되는지 확인한다.

## 6. 장애 대응

| 증상 | 원인 후보 | 조치 |
| --- | --- | --- |
| `lancedb 패키지가 설치되어 있지 않습니다.` | 의존성 미설치 | `uv sync` 후 재실행 |
| `rag_chunks 컬렉션이 없습니다.` | ingestion 미수행 | `ingest_lancedb.py` 실행 |
| 검색 결과가 0건 | 데이터 미적재/벡터 차원 불일치 | ingestion 재실행, 차원 로그 점검 |

## 7. 비고

1. SQLite 엔진은 벡터 검색을 지원하지 않는다.
2. 파일 기반 벡터 검색은 LanceDB를 기본 경로로 사용한다.
