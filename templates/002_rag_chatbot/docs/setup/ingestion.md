# Ingestion

## 입력 형식

- `.pdf`
- `.docx`
- `.md`
- `.markdown`

## CLI

- `--backend`: `lancedb`, `postgres`, `elasticsearch`
- `--input-root`: 기본 `data/ingestion-doc`
- `--chunk-workers`: 기본 `0`
- `--sample`: 확장자별 1개 파일만 처리
- `--reset`: 적재 전에 기존 컬렉션/테이블/인덱스 삭제 후 재생성

## 파이프라인

1. 입력 경로 스캔과 파일 파싱
2. 레이아웃 기반 청킹
3. 표/이미지 주석 생성
4. 임베딩 생성
5. 선택한 backend로 upsert

## 현재 동작 범위

- ingestion backend 선택은 가능하지만 online retrieval는 현재 LanceDB 경로를 직접 사용한다.
- 다른 backend로 적재해도 Chat 검색 경로가 자동으로 바뀌지 않는다.
- 차원이 바뀌면 `INGESTION_EMBEDDING_DIMENSION_MISMATCH`가 날 수 있으므로 `--reset` 재적재가 필요할 수 있다.
