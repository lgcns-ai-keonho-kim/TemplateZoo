"""
목적: ingestion 텍스트를 청크 단위로 분할한다.
설명: 파일 추출 결과를 구조 단위(헤더/문단/불렛/표) 우선으로 결합해 청크를 생성한다.
디자인 패턴: 함수형 변환 모듈
참조: ingestion/core/file_parser.py, ingestion/steps/chunk_step.py
"""

from __future__ import annotations

import os
import re
import traceback
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import TypedDict

from ingestion.core.file_parser import extract_text_by_file
from ingestion.core.types import IngestionChunk

_DEFAULT_MAX_CHARS = 1024
_MIN_CHUNK_CHARS = 120
_JOINER = "\n\n"
_BULLET_PATTERN = re.compile(r"^\s*(?:[-*+•◦▪‣]|\d+[.)]|[a-zA-Z][.)])\s+")
_HEADING_PATTERN = re.compile(r"^\s*#{1,6}\s+")


class _StructuralUnit(TypedDict):
    """구조 단위 텍스트 조각."""

    text: str
    metadata: dict[str, object]
    segment_type: str


def chunk_sources(
    paths: list[Path],
    *,
    max_chars: int = _DEFAULT_MAX_CHARS,
    overlap_chars: int = 120,
    workers: int | None = None,
) -> list[IngestionChunk]:
    """레이아웃 기반 텍스트를 청크로 분할한다."""

    del overlap_chars
    if not paths:
        print("[진행][chunk] 처리할 파일이 없습니다.")
        return []

    sorted_paths = sorted(paths)
    worker_count = _resolve_worker_count(file_count=len(sorted_paths), workers=workers)
    print(
        f"[진행][chunk] 청킹 시작: 파일 {len(sorted_paths)}개, 워커 {worker_count}개, "
        f"max_chars={int(max_chars)}, min_chunk_chars={_MIN_CHUNK_CHARS}"
    )
    path_args = [(str(path), int(max_chars)) for path in sorted_paths]

    chunks: list[IngestionChunk] = []
    next_index = 1
    if worker_count > 1:
        with ProcessPoolExecutor(max_workers=worker_count) as executor:
            row_iter = executor.map(_extract_and_chunk_document, path_args)
            for file_index, (path, chunk_rows) in enumerate(zip(sorted_paths, row_iter, strict=True), start=1):
                for body, metadata in chunk_rows:
                    chunk = IngestionChunk(
                        chunk_id=_make_chunk_id(next_index),
                        index=next_index,
                        file_name=path.name,
                        file_path=str(path),
                        body=body,
                        metadata=metadata,
                        emb_body=None,
                    )
                    chunks.append(chunk)
                    next_index += 1
                print(
                    f"[진행][chunk] 파일 완료: {file_index}/{len(sorted_paths)} "
                    f"({path.name}), 누적 청크 {len(chunks)}개"
                )
    else:
        for file_index, path in enumerate(sorted_paths, start=1):
            chunk_rows = _extract_and_chunk_document((str(path), int(max_chars)))
            for body, metadata in chunk_rows:
                chunk = IngestionChunk(
                    chunk_id=_make_chunk_id(next_index),
                    index=next_index,
                    file_name=path.name,
                    file_path=str(path),
                    body=body,
                    metadata=metadata,
                    emb_body=None,
                )
                chunks.append(chunk)
                next_index += 1
            print(
                f"[진행][chunk] 파일 완료: {file_index}/{len(sorted_paths)} "
                f"({path.name}), 누적 청크 {len(chunks)}개"
            )

    print(f"[진행][chunk] 청킹 종료: 총 청크 {len(chunks)}개")
    return chunks


def _extract_and_chunk_document(args: tuple[str, int]) -> list[tuple[str, dict[str, object]]]:
    """단일 문서에서 구조 단위 추출과 청킹을 수행한다."""

    path_raw, max_chars = args
    path = Path(path_raw)
    try:
        raw_rows = extract_text_by_file(path)
        units = _to_structural_units(raw_rows)
        return _pack_structural_units(units, max_chars=max_chars)
    except Exception as error:
        # 멀티프로세스 직렬화 오류(BrokenProcessPool)를 피하기 위해
        # 원본 예외 객체 대신 문자열 기반 RuntimeError로 변환한다.
        trace_text = traceback.format_exc(limit=8)
        raise RuntimeError(
            f"청킹 워커 실패: file={path.as_posix()}, error={error!s}\n{trace_text}"
        ) from None


def _to_structural_units(rows: list[tuple[str, dict[str, object]]]) -> list[_StructuralUnit]:
    """파서 출력을 구조 단위 목록으로 변환한다."""

    units: list[_StructuralUnit] = []
    synthetic_page_num = 1
    for row_text, row_metadata in rows:
        normalized_text = _normalize_text(str(row_text or ""))
        if not normalized_text:
            continue

        base_metadata = dict(row_metadata)
        if base_metadata.get("page_num") is None:
            base_metadata["page_num"] = synthetic_page_num
            synthetic_page_num += 1

        layout_type = str(base_metadata.get("layout_type", "")).strip().lower()
        if layout_type == "markdown":
            units.extend(_split_markdown_units(normalized_text, base_metadata))
            continue

        segment_type = _resolve_segment_type(normalized_text, base_metadata)
        units.append(
            {
                "text": normalized_text,
                "metadata": base_metadata,
                "segment_type": segment_type,
            }
        )
    return units


def _split_markdown_units(text: str, base_metadata: dict[str, object]) -> list[_StructuralUnit]:
    """Markdown 텍스트를 구조 단위로 분리한다."""

    lines = text.splitlines()
    units: list[_StructuralUnit] = []
    buffer: list[str] = []

    def flush_paragraph() -> None:
        if not buffer:
            return
        paragraph_text = _normalize_text("\n".join(buffer))
        buffer.clear()
        if not paragraph_text:
            return
        metadata = dict(base_metadata)
        metadata["block_type"] = "paragraph"
        metadata["heading_tag"] = "BODY"
        units.append(
            {
                "text": paragraph_text,
                "metadata": metadata,
                "segment_type": "paragraph",
            }
        )

    line_count = len(lines)
    index = 0
    while index < line_count:
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue

        if _HEADING_PATTERN.match(line):
            flush_paragraph()
            heading_level = min(6, max(1, len(stripped) - len(stripped.lstrip("#"))))
            heading_text = _normalize_text(stripped.lstrip("#").strip())
            if heading_text:
                metadata = dict(base_metadata)
                metadata["block_type"] = "heading"
                metadata["heading_level"] = heading_level
                metadata["heading_tag"] = f"H{heading_level}"
                units.append(
                    {
                        "text": heading_text,
                        "metadata": metadata,
                        "segment_type": "heading",
                    }
                )
            index += 1
            continue

        if _is_bullet_line(line):
            flush_paragraph()
            bullet_lines: list[str] = [line]
            index += 1
            while index < line_count:
                next_line = lines[index]
                next_stripped = next_line.strip()
                if not next_stripped:
                    break
                if _is_bullet_line(next_line) or _is_bullet_continuation(next_line):
                    bullet_lines.append(next_line)
                    index += 1
                    continue
                break
            bullet_text = _normalize_text("\n".join(bullet_lines))
            if bullet_text:
                metadata = dict(base_metadata)
                metadata["block_type"] = "bullet"
                metadata["heading_tag"] = "BODY"
                units.append(
                    {
                        "text": bullet_text,
                        "metadata": metadata,
                        "segment_type": "bullet",
                    }
                )
            continue

        buffer.append(line)
        index += 1

    flush_paragraph()
    return units


def _pack_structural_units(
    units: list[_StructuralUnit],
    *,
    max_chars: int,
) -> list[tuple[str, dict[str, object]]]:
    """구조 단위를 max_chars 기준으로 결합한다."""

    if not units:
        return []

    safe_max_chars = max(256, int(max_chars))
    groups: list[list[_StructuralUnit]] = []
    current_group: list[_StructuralUnit] = []

    for unit in units:
        # 이미지/표 블록은 반드시 독립 청크로 유지한다.
        if unit["segment_type"] in {"image", "table"}:
            if current_group:
                groups.append(current_group)
                current_group = []
            groups.append([unit])
            continue

        if not current_group:
            current_group = [unit]
            continue

        candidate_len = _units_length(current_group) + len(_JOINER) + len(unit["text"])
        if candidate_len <= safe_max_chars:
            current_group.append(unit)
            continue

        if _should_keep_structural_continuity(current_group, unit):
            current_group.append(unit)
            continue

        groups.append(current_group)
        current_group = [unit]

    if current_group:
        groups.append(current_group)

    groups = _merge_tiny_groups(groups)
    return [_finalize_group(group) for group in groups if group]


def _should_keep_structural_continuity(
    current_group: list[_StructuralUnit],
    next_unit: _StructuralUnit,
) -> bool:
    """구조 단위 미완료 상태인지 판단한다."""

    current_len = _units_length(current_group)
    if current_len < _MIN_CHUNK_CHARS:
        return True

    prev_unit = current_group[-1]
    prev_type = prev_unit["segment_type"]
    next_type = next_unit["segment_type"]

    if prev_type in {"image", "table"} or next_type in {"image", "table"}:
        return False
    if prev_type == "heading":
        return True
    if prev_type == "bullet" and next_type == "bullet":
        return True
    return _is_probable_continuation(prev_unit, next_unit)


def _is_probable_continuation(prev_unit: _StructuralUnit, next_unit: _StructuralUnit) -> bool:
    """짧은 텍스트/문장 단절 형태를 이어붙여야 하는지 판단한다."""

    prev_text = prev_unit["text"].strip()
    next_text = next_unit["text"].strip()
    if not prev_text or not next_text:
        return False

    prev_page = prev_unit["metadata"].get("page_num")
    next_page = next_unit["metadata"].get("page_num")
    if prev_page == next_page and (len(prev_text) < 48 or len(next_text) < 48):
        return True

    if prev_text.endswith(("-", "(", "/", "·", ":", ",")):
        return True
    if prev_text[-1] not in ".!?)]}\"'":
        first = next_text[0]
        if first.islower() or first.isdigit() or first in "([{":
            return True
    return False


def _merge_tiny_groups(groups: list[list[_StructuralUnit]]) -> list[list[_StructuralUnit]]:
    """과도하게 작은 그룹을 인접 그룹과 병합한다."""

    if not groups:
        return []

    merged: list[list[_StructuralUnit]] = []
    for group in groups:
        if not merged:
            merged.append(group)
            continue
        if _group_has_locked_unit(group):
            merged.append(group)
            continue
        if _group_has_locked_unit(merged[-1]):
            merged.append(group)
            continue
        if _units_length(group) < _MIN_CHUNK_CHARS:
            merged[-1] = merged[-1] + group
            continue
        merged.append(group)

    if (
        len(merged) > 1
        and _units_length(merged[0]) < _MIN_CHUNK_CHARS
        and not _group_has_locked_unit(merged[0])
        and not _group_has_locked_unit(merged[1])
    ):
        merged[1] = merged[0] + merged[1]
        merged = merged[1:]
    return merged


def _finalize_group(group: list[_StructuralUnit]) -> tuple[str, dict[str, object]]:
    """구조 단위 그룹을 최종 청크 텍스트/메타데이터로 변환한다."""

    body = _JOINER.join(unit["text"] for unit in group).strip()
    page_numbers: list[int] = []
    for unit in group:
        page_num = _to_int(unit["metadata"].get("page_num"))
        if page_num is None:
            continue
        page_numbers.append(page_num)

    metadata: dict[str, object] = {}
    if page_numbers:
        metadata["page_num"] = min(page_numbers)
    return body, metadata


def _units_length(group: list[_StructuralUnit]) -> int:
    if not group:
        return 0
    return sum(len(unit["text"]) for unit in group) + (len(group) - 1) * len(_JOINER)


def _resolve_segment_type(text: str, metadata: dict[str, object]) -> str:
    """텍스트와 메타데이터를 기반으로 구조 타입을 판별한다."""

    block_type = str(metadata.get("block_type", "")).strip().lower()
    if block_type == "image":
        return "image"
    if block_type == "table":
        return "table"
    if block_type == "heading" or metadata.get("heading_level") is not None:
        return "heading"
    if block_type == "bullet":
        return "bullet"
    if _looks_like_bullet_block(text):
        return "bullet"
    return "paragraph"


def _looks_like_bullet_block(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    bullet_count = sum(1 for line in lines if _is_bullet_line(line))
    return bullet_count >= max(1, len(lines) // 2)


def _is_bullet_line(line: str) -> bool:
    return bool(_BULLET_PATTERN.match(line))


def _is_bullet_continuation(line: str) -> bool:
    raw = str(line or "")
    return bool(raw.startswith("  ") or raw.startswith("\t"))


def _normalize_text(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _group_has_locked_unit(group: list[_StructuralUnit]) -> bool:
    return any(unit["segment_type"] in {"image", "table"} for unit in group)


def _to_int(value: object) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _make_chunk_id(index: int) -> str:
    return str(index)


def _resolve_worker_count(*, file_count: int, workers: int | None) -> int:
    """문서 수 기준으로 실제 워커 수를 계산한다."""

    if file_count <= 1:
        return 1

    if workers is None or workers <= 0:
        cpu_count = os.cpu_count() or 1
        return max(1, min(cpu_count, file_count))

    return max(1, min(int(workers), file_count))


__all__ = ["chunk_sources"]
