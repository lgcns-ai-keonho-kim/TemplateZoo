"""
목적: ingestion 파이프라인 실행기를 제공한다.
설명: 백엔드 종류별 업서트 단계를 선택해 공통 청킹/주석/비동기 임베딩/적재 흐름을 수행한다.
디자인 패턴: 전략 패턴
참조: ingestion/steps/chunk_step.py, ingestion/steps/embedding_step.py, ingestion/steps/upsert_*.py
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from ingestion.core.types import IngestionChunk
from ingestion.steps.chunk_step import run_chunk_step
from ingestion.steps.embedding_step import run_embedding_step
from ingestion.steps.upsert_elasticsearch_step import run_upsert_elasticsearch_step
from ingestion.steps.upsert_lancedb_step import run_upsert_lancedb_step
from ingestion.steps.upsert_postgres_step import run_upsert_postgres_step
from rag_chatbot.integrations.embedding import EmbeddingClient
from rag_chatbot.shared.config import resolve_gemini_embedding_dim

BackendName = Literal["lancedb", "postgres", "elasticsearch"]


class UpsertStep(Protocol):
    """업서트 단계 호출 규약."""

    def __call__(
        self,
        chunks: list[IngestionChunk],
        *,
        embedder: Embeddings,
        reset: bool = False,
    ) -> None: ...


@dataclass(frozen=True)
class BackendSpec:
    """백엔드별 실행 사양."""

    name: BackendName
    upsert_step: UpsertStep
    embedder_name: str


class IngestionRunner:
    """백엔드 독립 ingestion 실행기."""

    _SPECS: dict[BackendName, BackendSpec] = {
        "lancedb": BackendSpec(
            name="lancedb",
            upsert_step=run_upsert_lancedb_step,
            embedder_name="ingest-lancedb-embedding",
        ),
        "postgres": BackendSpec(
            name="postgres",
            upsert_step=run_upsert_postgres_step,
            embedder_name="ingest-postgres-embedding",
        ),
        "elasticsearch": BackendSpec(
            name="elasticsearch",
            upsert_step=run_upsert_elasticsearch_step,
            embedder_name="ingest-elasticsearch-embedding",
        ),
    }

    def run(
        self,
        *,
        backend: BackendName,
        input_root: Path,
        chunk_workers: int = 0,
        sample: bool = False,
        reset: bool = False,
    ) -> None:
        """지정한 백엔드로 ingestion 전체 단계를 실행한다."""

        spec = self._resolve_spec(backend)
        # 표/이미지 주석 생성에 사용할 LLM을 먼저 준비한다.
        annotation_model = self._build_annotation_model()
        embedder = self._build_embedder(spec.embedder_name)

        print(
            f"[진행][ingest][{spec.name}] 시작: input_root={input_root}, "
            f"chunk_workers={int(chunk_workers)}, sample={bool(sample)}, reset={bool(reset)}"
        )
        chunks = run_chunk_step(
            input_root,
            chunk_workers=int(chunk_workers),
            sample=bool(sample),
            annotation_model=annotation_model,
        )
        print(f"[진행][ingest][{spec.name}] 청킹 완료: count={len(chunks)}")

        # 임베딩 단계는 내부에서 aembed_documents 배치 호출로 비동기 수행한다.
        chunks = run_embedding_step(chunks, embedder=embedder)
        print(f"[진행][ingest][{spec.name}] 임베딩 생성 완료")

        spec.upsert_step(
            chunks,
            embedder=embedder,
            reset=bool(reset),
        )
        print(f"[진행][ingest][{spec.name}] 업서트 완료")

    def _resolve_spec(self, backend: BackendName) -> BackendSpec:
        spec = self._SPECS.get(backend)
        if spec is not None:
            return spec
        supported = ", ".join(sorted(self._SPECS.keys()))
        raise ValueError(f"지원하지 않는 backend입니다: {backend}. 허용값: {supported}")

    def _build_annotation_model(self) -> BaseChatModel:
        """표/이미지 주석용 Gemini 모델을 생성한다."""

        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", ""),
            project=os.getenv("GEMINI_PROJECT", ""),
            thinking_level="minimal",
        )

    def _build_embedder(self, embedder_name: str) -> Embeddings:
        """임베딩 생성용 Gemini 임베더를 생성한다."""

        dimension = resolve_gemini_embedding_dim()
        return EmbeddingClient(
            model=GoogleGenerativeAIEmbeddings(
                model=os.getenv("GEMINI_EMBEDDING_MODEL", ""),
                project=os.getenv("GEMINI_PROJECT", ""),
                output_dimensionality=dimension,
            ),
            name=embedder_name,
        )


__all__ = ["BackendName", "BackendSpec", "IngestionRunner"]
