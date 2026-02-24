"""
목적: PDF 페이지 자산(텍스트/이미지) 추출 유틸을 제공한다.
설명: 페이지 병렬 처리, 이미지 후보 필터링, HDBSCAN 기반 클러스터링, 이미지 파일 저장을 담당한다.
디자인 패턴: 함수형 유틸 모듈
참조: ingestion/core/file_parser.py, ingestion/core/image_annotation.py
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from collections import Counter

import numpy as np

from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail

_MIN_IMAGE_PIXEL_AREA = 40_000
_MIN_IMAGE_DIMENSION = 120
_MIN_RENDERED_AREA = 30_000
_CLIP_PADDING_PT = 4.0
_RENDER_SCALE = 2.0
_DEFAULT_KO_FONT_NAME = "Noto Sans CJK KR"
_DEFAULT_FONT_SIZE_PT = 11.0

_HDBSCAN_IMPORT_FAILED = False
_HDBSCAN_RUNTIME_FAILED = False
_DEFAULT_KO_FONT_CACHE: str | None = None


@dataclass(frozen=True)
class PdfTextBlock:
    """PDF 텍스트 블록 데이터 모델."""

    text: str
    font_size: float | None
    font_name: str


@dataclass(frozen=True)
class PdfPageAsset:
    """PDF 페이지 단위 추출 결과 모델."""

    page_num: int
    text_blocks: list[PdfTextBlock]
    page_text: str
    image_paths: list[Path]


@dataclass(frozen=True)
class _ImageCandidate:
    """페이지 내 이미지 후보 데이터 모델."""

    xref: int
    rect: tuple[float, float, float, float]
    width: int
    height: int


def extract_pdf_page_assets(
    path: Path,
    *,
    page_workers: int | None = None,
) -> list[PdfPageAsset]:
    """PDF에서 페이지별 텍스트 블록과 이미지 파일 경로를 추출한다."""

    try:
        import fitz
    except ImportError as error:
        detail = ExceptionDetail(
            code="INGESTION_PDF_READER_MISSING",
            cause="pymupdf 패키지가 설치되어 있지 않습니다.",
        )
        raise BaseAppException("PDF ingestion을 위해 pymupdf가 필요합니다.", detail, error) from error

    try:
        with fitz.open(str(path)) as document:
            page_count = int(document.page_count)
    except Exception as error:
        detail = ExceptionDetail(
            code="INGESTION_PDF_OPEN_FAILED",
            cause=f"path={path}",
        )
        raise BaseAppException("PDF 파일을 열 수 없습니다.", detail, error) from error

    if page_count <= 0:
        return []

    worker_count = _resolve_page_worker_count(page_count=page_count, workers=page_workers)
    print(
        f"[진행][pdf] 페이지 자산 추출 시작: page_count={page_count}, "
        f"workers={worker_count}, file={path.name}"
    )

    args_list = [(str(path), page_index) for page_index in range(page_count)]
    results: list[PdfPageAsset] = []
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        page_results = executor.map(_extract_single_page_asset, args_list)
        for done_count, page_result in enumerate(page_results, start=1):
            results.append(page_result)
            print(f"[진행][pdf] 페이지 처리 {done_count}/{page_count} ({path.name})")

    results.sort(key=lambda item: item.page_num)
    print(f"[진행][pdf] 페이지 자산 추출 완료: file={path.name}")
    return results


def _extract_single_page_asset(args: tuple[str, int]) -> PdfPageAsset:
    """단일 PDF 페이지에서 텍스트/이미지 자산을 추출한다."""

    try:
        import fitz
    except ImportError as error:
        detail = ExceptionDetail(
            code="INGESTION_PDF_READER_MISSING",
            cause="pymupdf 패키지가 설치되어 있지 않습니다.",
        )
        raise BaseAppException("PDF ingestion을 위해 pymupdf가 필요합니다.", detail, error) from error

    path_raw, page_index = args
    source_path = Path(path_raw)
    with fitz.open(str(source_path)) as document:
        page = document.load_page(page_index)
        text_blocks = _extract_pdf_text_blocks(page)
        page_text = "\n".join(block.text for block in text_blocks).strip()
        image_paths = _extract_page_images(
            source_path=source_path,
            page=page,
            page_num=page_index + 1,
        )

    return PdfPageAsset(
        page_num=page_index + 1,
        text_blocks=text_blocks,
        page_text=page_text,
        image_paths=image_paths,
    )


def _extract_pdf_text_blocks(page: object) -> list[PdfTextBlock]:
    """PyMuPDF 페이지에서 텍스트 블록을 추출한다."""

    default_font_name = _resolve_default_korean_font_name()
    raw = page.get_text("dict")
    blocks: list[PdfTextBlock] = []
    for block in raw.get("blocks", []):
        if int(block.get("type", 0)) != 0:
            continue
        line_texts: list[str] = []
        font_sizes: list[float] = []
        font_names: list[str] = []
        for line in block.get("lines", []):
            span_texts: list[str] = []
            for span in line.get("spans", []):
                span_text = str(span.get("text") or "").strip()
                if not span_text:
                    continue
                span_texts.append(span_text)
                size = span.get("size")
                if isinstance(size, int | float):
                    font_sizes.append(float(size))
                font_name = str(span.get("font") or "").strip()
                if font_name:
                    font_names.append(font_name)
            if span_texts:
                line_texts.append(" ".join(span_texts))
        text = "\n".join(line_texts).strip()
        if not text:
            continue
        resolved_font_name = _pick_majority_font_name(font_names) or default_font_name
        blocks.append(
            PdfTextBlock(
                text=text,
                font_size=max(font_sizes) if font_sizes else _DEFAULT_FONT_SIZE_PT,
                font_name=resolved_font_name,
            )
        )
    return blocks


def _resolve_default_korean_font_name() -> str:
    """Ubuntu 환경의 기본 한글 폰트명을 결정한다."""

    global _DEFAULT_KO_FONT_CACHE
    if _DEFAULT_KO_FONT_CACHE:
        return _DEFAULT_KO_FONT_CACHE

    env_font = os.getenv("INGESTION_DEFAULT_KO_FONT", "").strip()
    if env_font:
        _DEFAULT_KO_FONT_CACHE = env_font
        return _DEFAULT_KO_FONT_CACHE

    try:
        result = subprocess.run(
            ["fc-match", "-f", "%{family}", _DEFAULT_KO_FONT_NAME],
            check=False,
            capture_output=True,
            text=True,
        )
        candidate = str(result.stdout or "").strip()
        if candidate:
            _DEFAULT_KO_FONT_CACHE = candidate
            return _DEFAULT_KO_FONT_CACHE
    except Exception:
        pass

    _DEFAULT_KO_FONT_CACHE = _DEFAULT_KO_FONT_NAME
    return _DEFAULT_KO_FONT_CACHE


def _pick_majority_font_name(font_names: list[str]) -> str:
    """블록 내 가장 많이 등장한 폰트명을 반환한다."""

    if not font_names:
        return ""
    counts = Counter(font_names)
    return str(counts.most_common(1)[0][0])


def _extract_page_images(
    *,
    source_path: Path,
    page: object,
    page_num: int,
) -> list[Path]:
    """페이지 내 이미지 후보를 추출/필터링/클러스터링 후 파일로 저장한다."""

    candidates = _collect_image_candidates(page)
    filtered = [candidate for candidate in candidates if _is_candidate_usable(candidate)]
    if not filtered:
        return []

    clusters = _cluster_candidates(filtered=filtered, page=page)
    return _save_cluster_images(
        source_path=source_path,
        page=page,
        page_num=page_num,
        clusters=clusters,
    )


def _collect_image_candidates(page: object) -> list[_ImageCandidate]:
    """페이지의 원시 이미지 후보를 수집한다."""

    candidates: list[_ImageCandidate] = []
    seen: set[tuple[int, float, float, float, float]] = set()
    for image_info in page.get_images(full=True):
        if not image_info:
            continue
        xref = int(image_info[0])
        width = int(image_info[2] or 0)
        height = int(image_info[3] or 0)
        if xref <= 0 or width <= 0 or height <= 0:
            continue
        try:
            rects = page.get_image_rects(xref)
        except Exception:
            continue
        for rect in rects:
            key = (
                xref,
                round(float(rect.x0), 2),
                round(float(rect.y0), 2),
                round(float(rect.x1), 2),
                round(float(rect.y1), 2),
            )
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                _ImageCandidate(
                    xref=xref,
                    rect=(
                        float(rect.x0),
                        float(rect.y0),
                        float(rect.x1),
                        float(rect.y1),
                    ),
                    width=width,
                    height=height,
                )
            )
    return candidates


def _is_candidate_usable(candidate: _ImageCandidate) -> bool:
    """도형/아이콘 가능성이 높은 후보를 방어적으로 제거한다."""

    if candidate.width < _MIN_IMAGE_DIMENSION or candidate.height < _MIN_IMAGE_DIMENSION:
        return False
    if candidate.width * candidate.height < _MIN_IMAGE_PIXEL_AREA:
        return False

    x0, y0, x1, y1 = candidate.rect
    rect_width = max(0.0, x1 - x0)
    rect_height = max(0.0, y1 - y0)
    if rect_width < 12.0 or rect_height < 12.0:
        return False
    aspect_ratio = max(rect_width, 1.0) / max(rect_height, 1.0)
    if aspect_ratio > 8.0 or aspect_ratio < 0.12:
        return False
    return True


def _cluster_candidates(filtered: list[_ImageCandidate], page: object) -> list[list[_ImageCandidate]]:
    """HDBSCAN으로 페이지 내 이미지 후보를 묶어 하나의 덩어리로 만든다."""

    if len(filtered) == 1:
        return [[filtered[0]]]

    page_width = max(1.0, float(page.rect.width))
    page_height = max(1.0, float(page.rect.height))
    page_area = max(1.0, page_width * page_height)
    features = []
    for candidate in filtered:
        x0, y0, x1, y1 = candidate.rect
        cx = ((x0 + x1) * 0.5) / page_width
        cy = ((y0 + y1) * 0.5) / page_height
        area_norm = ((x1 - x0) * (y1 - y0)) / page_area
        aspect = max((x1 - x0), 1.0) / max((y1 - y0), 1.0)
        features.append([cx, cy, area_norm, aspect])

    labels = _run_hdbscan(np.asarray(features, dtype=float))
    clustered: dict[int, list[_ImageCandidate]] = {}
    for idx, label in enumerate(labels):
        if int(label) < 0:
            clustered[-(idx + 1)] = [filtered[idx]]
            continue
        clustered.setdefault(int(label), []).append(filtered[idx])

    groups = list(clustered.values())
    groups.sort(key=lambda items: (_group_rect(items)[1], _group_rect(items)[0]))
    return groups


def _run_hdbscan(features: np.ndarray) -> np.ndarray:
    """HDBSCAN 라벨을 계산한다. 실패 시 전부 단독 클러스터로 처리한다."""

    global _HDBSCAN_IMPORT_FAILED
    global _HDBSCAN_RUNTIME_FAILED

    try:
        from sklearn.cluster import HDBSCAN
    except Exception as error:  # pragma: no cover - 런타임 의존성 분기
        if not _HDBSCAN_IMPORT_FAILED:
            print(f"[진행][pdf-image] HDBSCAN import 실패, 단독 처리로 전환: {error}")
            _HDBSCAN_IMPORT_FAILED = True
        return np.full(shape=(len(features),), fill_value=-1, dtype=int)

    try:
        model = HDBSCAN(
            min_cluster_size=2,
            min_samples=1,
            cluster_selection_epsilon=0.08,
            metric="euclidean",
            copy=False,
        )
        return np.asarray(model.fit_predict(features), dtype=int)
    except Exception as error:  # pragma: no cover - 외부 알고리즘 오류 분기
        if not _HDBSCAN_RUNTIME_FAILED:
            print(f"[진행][pdf-image] HDBSCAN 실행 실패, 단독 처리로 전환: {error}")
            _HDBSCAN_RUNTIME_FAILED = True
        return np.full(shape=(len(features),), fill_value=-1, dtype=int)


def _save_cluster_images(
    *,
    source_path: Path,
    page: object,
    page_num: int,
    clusters: list[list[_ImageCandidate]],
) -> list[Path]:
    """클러스터 결과를 이미지 파일로 저장한다."""

    try:
        import fitz
    except ImportError as error:
        detail = ExceptionDetail(
            code="INGESTION_PDF_READER_MISSING",
            cause="pymupdf 패키지가 설치되어 있지 않습니다.",
        )
        raise BaseAppException("PDF ingestion을 위해 pymupdf가 필요합니다.", detail, error) from error

    output_dir = Path("data/images") / _sanitize_name(source_path.stem)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[Path] = []
    for cluster_index, cluster in enumerate(clusters, start=1):
        x0, y0, x1, y1 = _group_rect(cluster)
        clip = fitz.Rect(x0, y0, x1, y1)
        clip = _expand_rect(clip=clip, page_rect=page.rect, padding_pt=_CLIP_PADDING_PT)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(_RENDER_SCALE, _RENDER_SCALE), clip=clip, alpha=False)
        if not _is_rendered_image_usable(pixmap):
            continue
        if _looks_like_shape(pixmap):
            continue
        signature = _build_signature(source_path, page_num, cluster_index, clip)
        output_name = f"p{page_num:04d}_img{cluster_index:03d}_{signature}.png"
        output_path = output_dir / output_name
        pixmap.save(str(output_path))
        saved_paths.append(output_path)
    return saved_paths


def _group_rect(cluster: list[_ImageCandidate]) -> tuple[float, float, float, float]:
    """클러스터 후보들의 합집합 bbox를 계산한다."""

    x0 = min(item.rect[0] for item in cluster)
    y0 = min(item.rect[1] for item in cluster)
    x1 = max(item.rect[2] for item in cluster)
    y1 = max(item.rect[3] for item in cluster)
    return x0, y0, x1, y1


def _expand_rect(*, clip: object, page_rect: object, padding_pt: float) -> object:
    """bbox를 page 범위 내에서 살짝 확장한다."""

    x0 = max(float(page_rect.x0), float(clip.x0) - float(padding_pt))
    y0 = max(float(page_rect.y0), float(clip.y0) - float(padding_pt))
    x1 = min(float(page_rect.x1), float(clip.x1) + float(padding_pt))
    y1 = min(float(page_rect.y1), float(clip.y1) + float(padding_pt))
    return type(clip)(x0, y0, x1, y1)


def _is_rendered_image_usable(pixmap: object) -> bool:
    """렌더링된 이미지가 저장할 가치가 있는지 판단한다."""

    width = int(getattr(pixmap, "width", 0))
    height = int(getattr(pixmap, "height", 0))
    if width < _MIN_IMAGE_DIMENSION or height < _MIN_IMAGE_DIMENSION:
        return False
    if width * height < _MIN_RENDERED_AREA:
        return False
    return True


def _looks_like_shape(pixmap: object) -> bool:
    """단색 도형/배경 박스 가능성이 높은 이미지를 제거한다."""

    samples = getattr(pixmap, "samples", b"")
    width = int(getattr(pixmap, "width", 0))
    height = int(getattr(pixmap, "height", 0))
    channels = int(getattr(pixmap, "n", 0))
    if not samples or width <= 0 or height <= 0 or channels <= 0:
        return True

    arr = np.frombuffer(samples, dtype=np.uint8)
    try:
        arr = arr.reshape((height, width, channels))
    except ValueError:
        return True

    if channels >= 3:
        rgb = arr[:, :, :3]
    else:
        rgb = np.repeat(arr[:, :, :1], repeats=3, axis=2)
    gray = rgb.mean(axis=2)
    std = float(gray.std())
    unique_ratio = float(np.unique(gray.astype(np.uint8)).size) / 256.0
    return std < 6.0 and unique_ratio < 0.08


def _build_signature(
    source_path: Path,
    page_num: int,
    cluster_index: int,
    clip: object,
) -> str:
    """파일명 충돌 방지를 위한 짧은 서명을 생성한다."""

    raw = (
        f"{source_path.as_posix()}|{page_num}|{cluster_index}|"
        f"{float(clip.x0):.2f}|{float(clip.y0):.2f}|{float(clip.x1):.2f}|{float(clip.y1):.2f}"
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]


def _sanitize_name(text: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in text).strip("_") or "doc"


def _resolve_page_worker_count(*, page_count: int, workers: int | None) -> int:
    """페이지 병렬 처리 워커 수를 계산한다."""

    if page_count <= 1:
        return 1

    if workers is None or workers <= 0:
        cpu_count = os.cpu_count() or 1
        return max(1, min(cpu_count, page_count, 8))

    return max(1, min(int(workers), page_count))


__all__ = ["PdfPageAsset", "PdfTextBlock", "extract_pdf_page_assets"]
