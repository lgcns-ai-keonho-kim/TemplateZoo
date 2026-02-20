"""
목적: PostgreSQL(pgvector) ingestion 실행 스크립트를 제공한다.
설명: data/ingestion-doc 문서를 청킹/임베딩/pgvector 업서트 순서로 처리한다.
디자인 패턴: 스크립트 오케스트레이션
참조: ingestion/steps/*.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# `python ingestion/ingest_postgres.py` 실행 시 프로젝트 루트를 import 경로에 보정한다.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingestion.steps.chunk_step import run_chunk_step
from ingestion.steps.embedding_step import run_embedding_step
from ingestion.steps.upsert_postgres_step import run_upsert_postgres_step


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PostgreSQL ingestion 실행")
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
        help="청킹 단계 멀티프로세스 워커 수 (0 이하이면 자동)",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="확장자별 1개 파일만 샘플 처리",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print(
        f"[진행][ingest][postgres] 시작: input_root={args.input_root}, "
        f"chunk_workers={int(args.chunk_workers)}, sample={bool(args.sample)}"
    )
    chunks = run_chunk_step(
        args.input_root,
        chunk_workers=int(args.chunk_workers),
        sample=bool(args.sample),
    )
    print(f"[진행][ingest][postgres] 청킹 완료: count={len(chunks)}")

    chunks = run_embedding_step(chunks)
    print("[진행][ingest][postgres] 임베딩 생성 완료")

    run_upsert_postgres_step(chunks)
    print("[진행][ingest][postgres] 업서트 완료")


if __name__ == "__main__":
    main()

# 기본 실행(권장): uv run python ingestion/ingest_sqlite_vec.py --input-root data/ingestion-doc
# Elasticsearch 대체 실행: uv run python ingestion/ingest_elasticsearch.py --input-root data/ingestion-doc
