"""
목적: LanceDB 벡터 저장소 데이터를 빠르게 확인하는 스크립트를 제공한다.
설명: ingestion 이후 rag_chunks 컬렉션에서 파일 메타데이터와 본문 전체를 조회해 JSON으로 출력한다.
디자인 패턴: 절차형 유틸 스크립트
참조: src/rag_chatbot/integrations/db/engines/lancedb/engine.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

try:
    import lancedb
except ImportError as error:  # pragma: no cover - 실행 환경 의존
    raise RuntimeError("lancedb 패키지가 설치되어 있지 않습니다.") from error

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")


_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DEFAULT_LANCEDB_URI = (
    str(os.getenv("LANCEDB_URI", "data/db/vector")).strip() or "data/db/vector"
)
_DEFAULT_TABLE_NAME = "rag_chunks"


def quick_view_lancedb(
    lancedb_uri: str,
    table_name: str,
    limit: int = 10,
    file_contains: str | None = None,
) -> list[dict[str, Any]]:
    """LanceDB rag 컬렉션에서 결과 일부를 조회한다."""

    safe_table_name = _validate_identifier(table_name)
    safe_limit = max(1, int(limit))

    database = lancedb.connect(lancedb_uri)
    table_names = _list_table_names(database)
    if safe_table_name not in table_names:
        legacy_uri = _find_existing_table_uri(
            table_name=safe_table_name,
            candidates=["data/db/lancedb", "data/db/vector"],
        )
        guidance = ""
        if legacy_uri and legacy_uri != lancedb_uri:
            guidance = (
                " "
                f"다음 명령으로 확인할 수 있습니다: "
                f"`uv run python check_db.py --lancedb-uri {legacy_uri} --table {safe_table_name} --limit {safe_limit}`"
            )
        raise RuntimeError(
            f"컬렉션이 존재하지 않습니다: {safe_table_name}. "
            f"현재 경로={lancedb_uri}, 현재 테이블={table_names}.{guidance}"
        )

    table = database.open_table(safe_table_name)
    builder = table.search().select(
        ["chunk_id", "index", "file_name", "file_path", "body", "metadata"]
    )

    if file_contains:
        escaped = _escape_sql_like(file_contains)
        builder = builder.where(f"file_name LIKE '%{escaped}%'")

    rows = builder.limit(safe_limit).to_arrow().to_pylist()
    return [_normalize_row(row) for row in rows]


def _list_table_names(database) -> list[str]:
    result = database.list_tables()
    if isinstance(result, list):
        return [str(name) for name in result]
    tables = getattr(result, "tables", None)
    if isinstance(tables, list):
        return [str(name) for name in tables]
    return []


def _find_existing_table_uri(table_name: str, candidates: list[str]) -> str | None:
    for candidate in candidates:
        table_path = Path(candidate) / f"{table_name}.lance"
        if table_path.exists():
            return candidate
    return None


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    body = str(row.get("body") or "")
    metadata = _parse_metadata(row.get("metadata"))
    return {
        "chunk_id": row.get("chunk_id"),
        "index": row.get("index"),
        "file_name": row.get("file_name"),
        "file_path": row.get("file_path"),
        "body": body,
        "body_length": len(body),
        "metadata": metadata,
    }


def _parse_metadata(value: object) -> object:
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return value
    return value


def _validate_identifier(identifier: str) -> str:
    candidate = str(identifier or "").strip()
    if not _IDENTIFIER_PATTERN.fullmatch(candidate):
        raise ValueError(f"지원하지 않는 테이블명 형식입니다: {identifier!r}")
    return candidate


def _escape_sql_like(text: str) -> str:
    return str(text).replace("'", "''")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LanceDB 컬렉션 데이터를 빠르게 확인한다."
    )
    parser.add_argument(
        "--lancedb-uri",
        default=_DEFAULT_LANCEDB_URI,
        help=f"LanceDB 경로 (기본값: {_DEFAULT_LANCEDB_URI})",
    )
    parser.add_argument(
        "--table",
        default=_DEFAULT_TABLE_NAME,
        help=f"조회할 컬렉션 이름 (기본값: {_DEFAULT_TABLE_NAME})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="조회할 최대 레코드 수 (기본값: 50)",
    )
    parser.add_argument(
        "--file-contains",
        default=None,
        help="file_name 부분 문자열 필터",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    rows = quick_view_lancedb(
        lancedb_uri=str(args.lancedb_uri),
        table_name=str(args.table),
        limit=int(args.limit),
        file_contains=(str(args.file_contains).strip() or None)
        if args.file_contains is not None
        else None,
    )
    print(json.dumps(rows, ensure_ascii=False, indent=2))
