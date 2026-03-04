"""
목적: PDF 페이지 캡처 유틸을 제공한다.
설명: 지정된 PDF 페이지를 이미지로 렌더링해 페이지 번호별 파일 경로를 반환한다.
      표/이미지 주석 단계의 입력 이미지를 생성할 때 사용한다.
디자인 패턴: 함수형 유틸 모듈
참조: ingestion/core/file_parser.py, ingestion/core/table_annotation.py
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail

_RENDER_SCALE = 2.0


def capture_pdf_pages(
    path: Path,
    *,
    page_numbers: Sequence[int],
) -> dict[int, Path]:
    """지정한 PDF 페이지를 캡처해 페이지 번호별 이미지 경로를 반환한다."""

    normalized_pages = sorted({int(page_num) for page_num in page_numbers if int(page_num) > 0})
    if not normalized_pages:
        return {}

    try:
        import fitz
    except ImportError as error:
        detail = ExceptionDetail(
            code="INGESTION_PDF_READER_MISSING",
            cause="pymupdf 패키지가 설치되어 있지 않습니다.",
        )
        raise BaseAppException("PDF 페이지 캡처를 위해 pymupdf가 필요합니다.", detail, error) from error

    output_dir = Path("data/images") / _sanitize_name(path.stem) / "pages"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with fitz.open(str(path)) as document:
            page_count = int(document.page_count)
            invalid_pages = [page_num for page_num in normalized_pages if page_num > page_count]
            if invalid_pages:
                detail = ExceptionDetail(
                    code="INGESTION_PDF_PAGE_OUT_OF_RANGE",
                    cause=f"path={path}, requested_pages={invalid_pages}, page_count={page_count}",
                )
                raise BaseAppException("PDF 페이지 캡처 범위가 유효하지 않습니다.", detail)

            captured: dict[int, Path] = {}
            for page_num in normalized_pages:
                page = document.load_page(page_num - 1)
                pixmap = page.get_pixmap(
                    matrix=fitz.Matrix(_RENDER_SCALE, _RENDER_SCALE),
                    alpha=False,
                )
                output_path = output_dir / f"p{page_num:04d}_page.png"
                pixmap.save(str(output_path))
                captured[page_num] = output_path
    except BaseAppException:
        raise
    except Exception as error:
        detail = ExceptionDetail(
            code="INGESTION_PDF_PAGE_CAPTURE_FAILED",
            cause=f"path={path}, error={error!s}",
        )
        raise BaseAppException("PDF 페이지 캡처에 실패했습니다.", detail, error) from error

    return captured


def _sanitize_name(text: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in text).strip("_") or "doc"


__all__ = ["capture_pdf_pages"]
