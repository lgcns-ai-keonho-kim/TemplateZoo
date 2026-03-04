# LanceDB 구성 가이드

이 문서는 파일 기반 벡터 저장소를 LanceDB로 사용하는 절차를 정리한다.

## 1. 적용 범위

1. RAG 벡터 저장소를 로컬 파일 기반으로 운영할 때
2. ingestion 백엔드를 `lancedb`로 실행할 때
3. SQLite는 Chat 이력 저장 전용으로 유지할 때

## 2. 관련 코드

| 경로 | 역할 |
| --- | --- |
| `src/rag_chatbot/integrations/db/engines/lancedb/engine.py` | LanceDB CRUD/벡터 검색 엔진 |
| `src/rag_chatbot/core/chat/nodes/rag_retrieve_node.py` | RAG 검색 시 LanceDB 사용 |
| `ingestion/ingest.py` | 통합 ingestion CLI |
| `ingestion/steps/upsert_lancedb_step.py` | LanceDB 업서트 + `--reset` 처리 |
| `ingestion/core/db.py` | LanceDB 클라이언트/스키마/차원 검증 |

## 3. 환경 변수

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `LANCEDB_URI` | `data/db/vector` | LanceDB 디렉터리 경로 |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | ingestion/RAG 임베딩 모델 |
| `GEMINI_EMBEDDING_DIM` | `1024` | ingestion/RAG 벡터 차원 |

예시:

```env
LANCEDB_URI=data/db/vector
```

## 4. ingestion 실행

```bash
uv run python ingestion/ingest.py --backend lancedb --input-root data/ingestion-doc
```

### 자주 쓰는 옵션

1. `--sample`: 확장자별 1개 파일만 처리
2. `--chunk-workers <N>`: 청킹 워커 수 지정
3. `--reset`: 기존 `rag_chunks` 컬렉션 삭제 후 재생성

재적재 예시:

```bash
uv run python ingestion/ingest.py --backend lancedb --input-root data/ingestion-doc --reset
```

## 5. 동작 확인

1. `LANCEDB_URI` 경로에 `rag_chunks.lance`가 생성되는지 확인한다.
2. RAG 요청 시 `rag_retrieve_node`가 검색 결과를 반환하는지 확인한다.
3. Chat 이력은 `CHAT_DB_PATH`(SQLite)에 저장되는지 확인한다.

## 6. 장애 대응

| 증상 | 원인 후보 | 조치 |
| --- | --- | --- |
| `lancedb 패키지가 설치되어 있지 않습니다.` | 의존성 미설치 | `uv sync` 후 재실행 |
| `INGESTION_INPUT_NOT_FOUND` | 입력 경로 오류 | `--input-root` 경로 확인 |
| `INGESTION_EMBEDDING_DIMENSION_MISMATCH` | 기존 컬렉션 차원 불일치 | `--reset`으로 재생성 후 재실행 |
| `RAG_EMBEDDING_DIMENSION_MISMATCH` | RAG 검색 노드 차원 불일치 | ingestion 재실행 + 컬렉션 재생성 |
| 검색 결과가 0건 | 데이터 미적재/질의 불일치 | ingestion 재실행 및 입력 데이터 점검 |

## 7. 비고

1. SQLite 엔진은 벡터 검색을 지원하지 않는다.
2. LanceDB는 로컬 파일 기반이므로 백업/복원 정책을 별도로 운영해야 한다.
3. ingestion 상세 시퀀스는 `docs/setup/ingestion.md`를 참고한다.
