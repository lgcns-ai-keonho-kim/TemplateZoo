"""
목적: PostgreSQL(pgvector) ingestion 실행 스크립트를 제공한다.
설명: data/ingestion-doc 문서를 청킹/임베딩/pgvector 업서트 순서로 처리한다.
디자인 패턴: 스크립트 오케스트레이션
참조: ingestion/steps/*.py
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr

# `python ingestion/ingest_postgres.py` 실행 시 프로젝트 루트를 import 경로에 보정한다.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingestion.steps.chunk_step import run_chunk_step
from ingestion.steps.embedding_step import run_embedding_step
from ingestion.steps.upsert_postgres_step import run_upsert_postgres_step
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail

EMBED_MODEL = "text-embedding-3-small"
ANNOTATION_MODEL = "gpt-4o-mini"


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
        help="청킹 단계 워커 수 (모델 객체 주입 모드에서는 1로 고정)",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="확장자별 1개 파일만 샘플 처리",
    )
    return parser.parse_args()


def _resolve_openai_api_key() -> str:
    """OpenAI API 키를 검증해 반환한다."""

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        detail = ExceptionDetail(
            code="INGESTION_OPENAI_API_KEY_MISSING",
            cause="OPENAI_API_KEY 환경 변수가 비어 있습니다.",
        )
        raise BaseAppException("ingestion 실행을 위해 OPENAI_API_KEY가 필요합니다.", detail)
    return api_key


def _build_annotation_model(*, api_key: str) -> BaseChatModel:
    """표/이미지 주석용 ChatOpenAI 모델을 생성한다."""

    return ChatOpenAI(
        model=ANNOTATION_MODEL,
        api_key=SecretStr(api_key),
        temperature=0.0,
    )


def _build_embedder(*, api_key: str) -> Embeddings:
    """임베딩 생성용 OpenAI 임베더를 생성한다."""

    return OpenAIEmbeddings(
        model=EMBED_MODEL,
        api_key=api_key,
    )


def main() -> None:
    args = parse_args()
    api_key = _resolve_openai_api_key()
    annotation_model = _build_annotation_model(api_key=api_key)
    embedder = _build_embedder(api_key=api_key)

    print(
        f"[진행][ingest][postgres] 시작: input_root={args.input_root}, "
        f"chunk_workers={int(args.chunk_workers)}, sample={bool(args.sample)}"
    )
    chunks = run_chunk_step(
        args.input_root,
        chunk_workers=int(args.chunk_workers),
        sample=bool(args.sample),
        annotation_model=annotation_model,
    )
    print(f"[진행][ingest][postgres] 청킹 완료: count={len(chunks)}")

    chunks = run_embedding_step(chunks, embedder=embedder)
    print("[진행][ingest][postgres] 임베딩 생성 완료")

    run_upsert_postgres_step(chunks, embedder=embedder)
    print("[진행][ingest][postgres] 업서트 완료")


if __name__ == "__main__":
    main()

# LanceDB 실행: uv run python ingestion/ingest_lancedb.py --input-root data/ingestion-doc
# Elasticsearch 실행: uv run python ingestion/ingest_elasticsearch.py --input-root data/ingestion-doc
