"""
목적: ingestion 청킹 단계를 제공한다.
설명: 입력 디렉터리의 문서를 읽어 레이아웃 기반 청크 목록으로 변환한다.
디자인 패턴: 단계 함수
참조: ingestion/core/file_parser.py, ingestion/core/chunking.py
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.language_models import BaseChatModel

from ingestion.core.chunking import chunk_sources
from ingestion.core.file_parser import scan_input_files
from ingestion.core.types import IngestionChunk


def run_chunk_step(
    input_root: str | Path,
    *,
    chunk_workers: int | None = None,
    sample: bool = False,
    annotation_model: BaseChatModel,
) -> list[IngestionChunk]:
    """문서를 스캔해 청크 목록을 생성한다."""

    files = scan_input_files(input_root)
    print(f"[진행][chunk] 스캔 완료: 총 파일 {len(files)}개")
    if sample:
        files = _pick_one_file_per_extension(files)
        print(f"[진행][chunk] 샘플 모드 적용: 확장자별 파일 {len(files)}개")
    return chunk_sources(files, workers=chunk_workers, annotation_model=annotation_model)


def _pick_one_file_per_extension(files: list[Path]) -> list[Path]:
    """확장자별 첫 번째 파일만 선택한다."""

    selected: list[Path] = []
    seen_suffixes: set[str] = set()
    for file_path in files:
        suffix = file_path.suffix.lower()
        if suffix in seen_suffixes:
            continue
        selected.append(file_path)
        seen_suffixes.add(suffix)
    return selected


__all__ = ["run_chunk_step"]
