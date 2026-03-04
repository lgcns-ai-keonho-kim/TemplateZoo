"""
목적: 통합 ingestion CLI 스크립트를 제공한다.
설명: 단일 진입점에서 backend 인자를 받아 청킹/임베딩/업서트 파이프라인을 실행한다.
디자인 패턴: 파사드
참조: ingestion/core/runner.py

사용 방법:
1) 기본 실행 흐름
- 문서 청킹 -> 임베딩 생성 -> 백엔드 업서트 순서로 실행된다.
- `--backend`는 필수이며 `lancedb`, `postgres`, `elasticsearch` 중 하나를 선택한다.

2) 실행 예시
- LanceDB 적재
  `uv run python ingestion/ingest.py --backend lancedb --input-root data/ingestion-doc`
- PostgreSQL(pgvector) 적재
  `uv run python ingestion/ingest.py --backend postgres --input-root data/ingestion-doc`
- Elasticsearch 적재
  `uv run python ingestion/ingest.py --backend elasticsearch --input-root data/ingestion-doc`

3) 옵션 예시
- 샘플 실행(확장자별 1개 파일만 처리)
  `uv run python ingestion/ingest.py --backend lancedb --input-root data/ingestion-doc --sample`
- 청킹 워커 수 지정
  `uv run python ingestion/ingest.py --backend lancedb --chunk-workers 4`
- 기존 데이터 초기화 후 재적재
  `uv run python ingestion/ingest.py --backend lancedb --reset`

4) 옵션 설명
- `--backend`: 적재 대상 백엔드 선택(필수)
- `--input-root`: ingestion 대상 문서 루트 경로(기본값: `data/ingestion-doc`)
- `--chunk-workers`: 청킹 워커 수(기본값: `0`)
- `--sample`: 확장자별 1개 파일만 샘플 처리
- `--reset`: 업서트 전에 기존 컬렉션/테이블/인덱스를 삭제하고 재생성
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import cast

from dotenv import load_dotenv

# `python ingestion/ingest.py` 실행 시 프로젝트 루트를 import 경로에 보정한다.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingestion.core.runner import BackendName, IngestionRunner

_BACKEND_CHOICES: tuple[BackendName, ...] = ("lancedb", "postgres", "elasticsearch")


def parse_args(default_backend: BackendName | None = None) -> argparse.Namespace:
    """CLI 인자를 파싱한다."""

    parser = argparse.ArgumentParser(description="통합 ingestion 실행")
    if default_backend is None:
        parser.add_argument(
            "--backend",
            choices=_BACKEND_CHOICES,
            required=True,
            help="ingestion 백엔드 선택",
        )
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("data/ingestion-doc"),
        help="ingestion 대상 문서 루트 경로",
    )
    parser.add_argument(
        "--chunk-workers",
        type=int,
        default=0,
        help="청킹 단계 워커 수 (모델 객체 주입 모드에서는 1로 고정)",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="확장자별 1개 파일만 샘플 처리",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="업서트 전에 기존 컬렉션/테이블/인덱스를 삭제하고 재생성",
    )
    namespace = parser.parse_args()
    if default_backend is not None:
        namespace.backend = default_backend
    return namespace


def main(default_backend: BackendName | None = None) -> None:
    """통합 ingestion 실행 엔트리포인트."""

    # ingestion 스크립트 단독 실행 시에도 프로젝트 루트 `.env`를 로드한다.
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
    args = parse_args(default_backend=default_backend)
    backend = cast(BackendName, str(args.backend))
    runner = IngestionRunner()
    runner.run(
        backend=backend,
        input_root=Path(args.input_root),
        chunk_workers=int(args.chunk_workers),
        sample=bool(args.sample),
        reset=bool(args.reset),
    )


if __name__ == "__main__":
    main()
