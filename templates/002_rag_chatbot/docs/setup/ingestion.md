# Ingestion 실행 가이드

이 문서는 `ingestion/ingest.py`가 현재 어떤 단계로 문서를 적재하는지와, 유지보수 시 확인해야 할 포인트를 정리한다.

## 1. 현재 지원 입력 형식

- `.pdf`
- `.docx`
- `.md`
- `.markdown`

## 2. 현재 CLI

- `--backend`: `lancedb`, `postgres`, `elasticsearch`
- `--input-root`: 기본 `data/ingestion-doc`
- `--chunk-workers`
- `--sample`
- `--reset`

## 3. 현재 파이프라인

1. 입력 경로 스캔과 파일 파싱
2. 레이아웃 기반 청킹
3. 표/이미지 주석 생성
4. 임베딩 생성
5. 선택한 backend로 upsert

## 4. 현재 주의 지점

- online retrieval는 LanceDB 경로를 직접 사용하므로, 다른 backend로 적재해도 online path가 자동 전환되는 것은 아니다.
- 차원 변경 시 `INGESTION_EMBEDDING_DIMENSION_MISMATCH`를 피하려면 `--reset` 재적재 정책을 같이 가져가야 한다.
- 대량 적재 전에는 `--sample`로 파싱과 연결 이상 여부를 먼저 점검하는 편이 안전하다.

## 5. 유지보수/추가개발 포인트

- 새 backend를 추가하면 `ingestion/core/db.py`, `ingestion/core/runner.py`, backend별 upsert step, setup 문서를 함께 수정해야 한다.
- 파서 출력을 바꾸면 chunking, annotation, retrieval reference 포맷까지 영향이 이어진다.

## 6. 관련 문서

- `docs/setup/lancedb.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/setup/env.md`
- `docs/core/chat.md`
