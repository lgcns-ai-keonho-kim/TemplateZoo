"""
목적: PDF 표 추출 유틸을 제공한다.
설명: 페이지 병렬 처리로 PDF 표를 HTML 문자열 목록으로 변환한다.
디자인 패턴: 함수형 유틸 모듈
참조: ingestion/core/file_parser.py
"""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from html import escape
from pathlib import Path
from collections.abc import Sequence

from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail

_DEFAULT_KO_FONT_NAME = "Noto Sans CJK KR"
_DEFAULT_KO_FONT_BBOX = (-166.0, -225.0, 1000.0, 931.0)
_PDFMINER_FONT_PATCHED = False


def extract_pdf_tables_by_page(
    path: Path,
    *,
    page_workers: int | None = None,
) -> dict[int, list[str]]:
    """PDF 표를 페이지 번호별 HTML 목록으로 추출한다."""

    # 폰트 메타데이터 누락(FontBBox) 경고 노이즈를 억제한다.
    logging.getLogger("pdfminer.pdffont").setLevel(logging.ERROR)
    _ensure_pdfminer_font_fallback()

    try:
        import pdfplumber
    except ImportError as error:
        detail = ExceptionDetail(
            code="INGESTION_PDF_TABLE_READER_MISSING",
            cause="pdfplumber 패키지가 설치되어 있지 않습니다.",
        )
        raise BaseAppException("PDF 표 추출을 위해 pdfplumber가 필요합니다.", detail, error) from error

    try:
        with pdfplumber.open(str(path)) as pdf:
            page_count = len(pdf.pages)
    except Exception as error:
        detail = ExceptionDetail(
            code="INGESTION_PDF_TABLE_OPEN_FAILED",
            cause=f"path={path}",
        )
        raise BaseAppException("PDF 표 추출 중 파일 열기에 실패했습니다.", detail, error) from error

    if page_count <= 0:
        return {}

    worker_count = _resolve_worker_count(page_count=page_count, workers=page_workers)
    print(
        f"[진행][pdf-table] 표 추출 시작: page_count={page_count}, "
        f"workers={worker_count}, file={path.name}"
    )
    page_args = [(str(path), page_index) for page_index in range(page_count)]

    tables_by_page: dict[int, list[str]] = {}
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        page_iter = executor.map(_extract_single_page_tables, page_args)
        for done_count, (page_num, tables) in enumerate(page_iter, start=1):
            if tables:
                tables_by_page[page_num] = tables
            print(f"[진행][pdf-table] 페이지 처리 {done_count}/{page_count} ({path.name})")

    print(f"[진행][pdf-table] 표 추출 완료: file={path.name}")
    return tables_by_page


def _extract_single_page_tables(args: tuple[str, int]) -> tuple[int, list[str]]:
    """단일 페이지 표를 HTML로 변환한다."""

    try:
        import pdfplumber
    except ImportError as error:
        detail = ExceptionDetail(
            code="INGESTION_PDF_TABLE_READER_MISSING",
            cause="pdfplumber 패키지가 설치되어 있지 않습니다.",
        )
        raise BaseAppException("PDF 표 추출을 위해 pdfplumber가 필요합니다.", detail, error) from error

    path_raw, page_index = args
    source_path = Path(path_raw)
    page_num = page_index + 1

    try:
        with pdfplumber.open(str(source_path)) as pdf:
            if page_index >= len(pdf.pages):
                return page_num, []
            page = pdf.pages[page_index]
            raw_tables = page.extract_tables() or []
    except Exception as error:
        print(
            f"[진행][pdf-table] 페이지 추출 실패: file={source_path.name}, "
            f"page={page_num}, cause={error}"
        )
        return page_num, []

    html_tables: list[str] = []
    for raw_table in raw_tables:
        html = _table_matrix_to_html(raw_table)
        if not html:
            continue
        html_tables.append(html)
    return page_num, html_tables


def _table_matrix_to_html(raw_table: object) -> str:
    """pdfplumber 표 행렬을 HTML 테이블 문자열로 변환한다."""

    if not isinstance(raw_table, list):
        return ""

    row_html_list: list[str] = []
    for raw_row in raw_table:
        if not isinstance(raw_row, list):
            continue

        has_non_empty_cell = False
        cell_html_list: list[str] = []
        for raw_cell in raw_row:
            value = "" if raw_cell is None else str(raw_cell)
            normalized = value.strip()
            if normalized:
                has_non_empty_cell = True
            escaped_lines = [escape(line.strip()) for line in value.splitlines() if line.strip()]
            if escaped_lines:
                cell_value = "<br/>".join(escaped_lines)
            else:
                cell_value = ""
            cell_html_list.append(f"<td>{cell_value}</td>")

        if not cell_html_list:
            continue
        if not has_non_empty_cell:
            continue
        row_html_list.append(f"<tr>{''.join(cell_html_list)}</tr>")

    if not row_html_list:
        return ""
    return f"<table><tbody>{''.join(row_html_list)}</tbody></table>"


def _resolve_worker_count(*, page_count: int, workers: int | None) -> int:
    if page_count <= 1:
        return 1
    if workers is None or workers <= 0:
        cpu_count = os.cpu_count() or 1
        return max(1, min(cpu_count, page_count, 8))
    return max(1, min(int(workers), page_count))


def _ensure_pdfminer_font_fallback() -> None:
    """pdfminer FontBBox 누락 시 기본 bbox를 반환하도록 패치한다."""

    global _PDFMINER_FONT_PATCHED
    if _PDFMINER_FONT_PATCHED:
        return

    try:
        from pdfminer import pdffont
    except Exception as error:
        print(f"[진행][pdf-table] pdfminer 폰트 fallback 적용 생략: {error}")
        return

    original_parse_bbox = pdffont.PDFFont._parse_bbox

    def _patched_parse_bbox(descriptor: object) -> tuple[float, float, float, float]:
        bbox = original_parse_bbox(descriptor)
        if _is_zero_bbox(bbox):
            return _DEFAULT_KO_FONT_BBOX
        return bbox

    pdffont.PDFFont._parse_bbox = staticmethod(_patched_parse_bbox)
    _PDFMINER_FONT_PATCHED = True
    print(
        f"[진행][pdf-table] FontBBox fallback 적용: "
        f"font={_DEFAULT_KO_FONT_NAME}, bbox={_DEFAULT_KO_FONT_BBOX}"
    )


def _is_zero_bbox(bbox: object) -> bool:
    """bbox가 0 사각형인지 판단한다."""

    if not isinstance(bbox, Sequence):
        return False
    if len(bbox) != 4:
        return False
    try:
        return all(abs(float(value)) <= 1e-9 for value in bbox)
    except (TypeError, ValueError):
        return False


__all__ = ["extract_pdf_tables_by_page"]
