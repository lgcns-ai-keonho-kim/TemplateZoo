# Ingestion 실행 가이드

이 문서는 통합 ingestion 엔트리포인트인 `ingestion/ingest.py`의 실행 방법과 내부 처리 시퀀스를 코드 기준으로 정리한다.

## 1. 적용 범위

1. RAG 검색용 `rag_chunks` 데이터 적재
2. 문서 파싱/청킹/임베딩/백엔드 업서트 일괄 실행
3. 백엔드별 초기화(`--reset`)와 차원 검증 정책 확인

## 2. 관련 코드

| 경로 | 역할 |
| --- | --- |
| `ingestion/ingest.py` | 통합 CLI 엔트리포인트 |
| `ingestion/core/runner.py` | 백엔드 선택, 단계 실행 오케스트레이션 |
| `ingestion/steps/chunk_step.py` | 파일 스캔 + 청킹 단계 |
| `ingestion/steps/embedding_step.py` | 임베딩 단계 래퍼 |
| `ingestion/core/enrichment.py` | 비동기 배치 임베딩(`aembed_documents`) |
| `ingestion/core/pdf_assets.py` | PDF 페이지 텍스트/이미지 자산 추출 |
| `ingestion/core/pdf_page_capture.py` | PDF 전체 페이지 캡처 이미지 생성 |
| `ingestion/core/table_annotation.py` | 표 주석 생성(`[TBL]`) |
| `ingestion/core/image_annotation.py` | 이미지 주석 생성(`[IMG]`) |
| `ingestion/steps/upsert_lancedb_step.py` | LanceDB 업서트 |
| `ingestion/steps/upsert_postgres_step.py` | PostgreSQL 업서트 |
| `ingestion/steps/upsert_elasticsearch_step.py` | Elasticsearch 업서트 |
| `ingestion/core/file_parser.py` | PDF/DOCX/Markdown 파싱 |

## 3. 지원 입력 형식

`SUPPORTED_SUFFIXES` 기준:

1. `.pdf`
2. `.docx`
3. `.md`
4. `.markdown`

## 4. 빠른 실행

### 4-1. 기본 실행

```bash
uv run python ingestion/ingest.py --backend lancedb --input-root data/ingestion-doc
```

### 4-2. 백엔드별 실행

```bash
# LanceDB
uv run python ingestion/ingest.py --backend lancedb --input-root data/ingestion-doc

# PostgreSQL
uv run python ingestion/ingest.py --backend postgres --input-root data/ingestion-doc

# Elasticsearch
uv run python ingestion/ingest.py --backend elasticsearch --input-root data/ingestion-doc
```

### 4-3. 재적재/샘플 실행

```bash
# 기존 rag_chunks를 삭제하고 재적재
uv run python ingestion/ingest.py --backend lancedb --input-root data/ingestion-doc --reset

# 확장자별 1개 파일만 샘플 처리
uv run python ingestion/ingest.py --backend lancedb --input-root data/ingestion-doc --sample

# 청킹 워커 지정
uv run python ingestion/ingest.py --backend lancedb --chunk-workers 4
```

## 5. CLI 옵션

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--backend` | 없음(필수) | `lancedb`, `postgres`, `elasticsearch` 중 선택 |
| `--input-root` | `data/ingestion-doc` | 입력 문서 루트 경로 |
| `--chunk-workers` | `0` | 청킹 워커 수 |
| `--sample` | `False` | 확장자별 1개 파일만 처리 |
| `--reset` | `False` | 업서트 전 기존 컬렉션/테이블/인덱스 삭제 |

## 6. 내부 처리 시퀀스

`IngestionRunner.run()` 기준:

1. 주석 모델 생성
- `ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", ""), project=os.getenv("GEMINI_PROJECT", ""), thinking_level="minimal")`

2. 임베더 생성
- `EmbeddingClient(GoogleGenerativeAIEmbeddings(...))`
- 차원은 `resolve_gemini_embedding_dim()`으로 결정

3. 청킹 단계 (`run_chunk_step`)
- 입력 디렉터리 스캔
- 파일별 파싱 후 레이아웃 기반 청크 생성

4. 임베딩 단계 (`run_embedding_step`)
- `attach_embeddings()`에서 **비동기 배치** 임베딩 수행
- `aembed_documents()`를 배치 단위로 호출
- 배치 기본 크기: `32`

5. 업서트 단계
- 선택한 backend 전용 upsert step 실행
- 기존 벡터가 있으면 차원 일치 검증 후 저장

## 7. PDF/DOCX 파싱 동작

### 7-1. PDF

1. 페이지 자산 추출: 텍스트 블록 + 페이지 내 이미지 후보 경로
2. **모든 페이지를 캡처 이미지로 저장** (`data/images/<문서명>/pages`)
3. 표 주석 생성
- 표 HTML + 페이지 캡처 이미지 + 앞/현재/뒤 페이지 문맥 텍스트 기반으로 `<SUMMARY>`, `<DESCRIPTION>` 생성
- 저장 본문은 `[TBL] ... [/TBL]`이며 내부에 `<TBL>HTML 표</TBL>`를 포함
4. 이미지 주석 생성
- 페이지에 이미지가 존재하면 페이지 캡처 이미지를 기준으로 이미지 주석 1개 생성(페이지 단위)
- 저장 본문은 `[IMG] ... [/IMG]`이며 `<PATH>`, `<SUMMARY>`, `<DESCRIPTION>`를 포함

### 7-2. DOCX

1. 문단/표 순서를 유지해 블록 파싱
2. 표는 HTML 직렬화 후 주석 생성
3. 현재 구현은 **DOCX 개별 이미지 추출/저장 파이프라인을 제공하지 않음**

## 8. `--reset` 동작

1. `lancedb`: 기존 컬렉션 삭제 후 재생성
2. `postgres`: 기존 테이블 삭제 후 재생성
3. `elasticsearch`: 기존 인덱스 삭제 후 재생성

`--reset` 없이 실행하면 기존 데이터가 유지된 상태에서 upsert가 수행된다.

## 9. 장애 대응

| 증상 | 원인 후보 | 조치 |
| --- | --- | --- |
| `지원하지 않는 backend입니다` | `--backend` 오입력 | `lancedb/postgres/elasticsearch` 중 하나로 재실행 |
| `ingestion 입력 경로를 찾을 수 없습니다` | `--input-root` 경로 오류 | 입력 경로 존재 여부 확인 |
| `비동기 임베딩 생성에 실패했습니다` | 임베딩 API 실패/네트워크 문제 | 환경 변수/모델 접근 권한 확인 후 재실행 |
| `INGESTION_EMBEDDING_DIMENSION_MISMATCH` | 기존 저장소 차원과 현재 차원 불일치 | `--reset`으로 재생성 후 재적재 |
| `RAG 검색 결과가 없습니다` | 적재 데이터 없음 또는 질의 미스 | ingestion 재실행 후 검색 재확인 |

## 10. 운영 확인 항목

1. `GEMINI_EMBEDDING_DIM`과 저장소 벡터 차원이 일치하는지 확인한다.
2. 백엔드 전환 시 `--backend`와 환경 변수를 함께 바꾼다.
3. 대규모 재적재 전에는 `--sample`로 파싱/연결 이상 여부를 먼저 점검한다.
4. 차원 정책을 변경한 경우 `--reset`을 사용해 기존 저장소를 재생성한다.

## 11. 관련 문서

- `docs/setup/lancedb.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/setup/env.md`
- `docs/integrations/embedding/README.md`
