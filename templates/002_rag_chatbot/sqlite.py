"""
목적: SQLite DB의 테이블 데이터를 빠르게 확인하는 스크립트를 제공한다.
설명: sqlite-vec(vec0) 확장을 명시적으로 로드한 뒤 지정 테이블을 조회한다.
디자인 패턴: 절차형 유틸 스크립트
참조: src/rag_chatbot/integrations/db/engines/sqlite/connection.py
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

try:
    import sqlite_vec
except ImportError:
    sqlite_vec = None


_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def quick_view(db_file: str | Path, table_name: str, limit: int = 10) -> list[dict[str, Any]]:
    """지정 테이블의 최근 레코드를 조회한다."""

    safe_table_name = _validate_identifier(table_name)
    safe_limit = max(1, int(limit))
    with sqlite3.connect(str(db_file)) as connection:
        _enable_wal(connection)
        sqlite_vec_loaded, sqlite_vec_error = _load_sqlite_vec(connection)

        if safe_table_name.startswith("vec_") and not sqlite_vec_loaded:
            raise RuntimeError(
                "vec0 가상 테이블 조회를 위해 sqlite-vec 확장 로딩이 필요합니다. "
                f"환경에 sqlite-vec이 설치되어 있는지 확인하세요. cause={sqlite_vec_error}"
            )

        query = _build_query(connection, safe_table_name, safe_limit)
        cursor = connection.execute(query)
        columns = [item[0] for item in (cursor.description or [])]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]


def _validate_identifier(identifier: str) -> str:
    """SQL 식별자(테이블명) 유효성을 검증한다."""

    candidate = str(identifier or "").strip()
    if not _IDENTIFIER_PATTERN.fullmatch(candidate):
        raise ValueError(f"지원하지 않는 테이블명 형식입니다: {identifier!r}")
    return candidate


def _enable_wal(connection: sqlite3.Connection) -> None:
    """읽기 경쟁 상황 완화를 위해 WAL 모드를 활성화한다."""

    connection.execute("PRAGMA journal_mode=WAL;")


def _load_sqlite_vec(connection: sqlite3.Connection) -> tuple[bool, str]:
    """sqlite-vec 확장을 로드한다."""

    if sqlite_vec is None:
        return False, "sqlite_vec 모듈을 import할 수 없습니다."
    try:
        connection.enable_load_extension(True)
        sqlite_vec.load(connection)
    except Exception as error:
        return False, str(error)
    return True, ""


def _build_query(connection: sqlite3.Connection, table_name: str, limit: int) -> str:
    """테이블 형태에 맞는 조회 쿼리를 생성한다."""

    try:
        connection.execute(f"SELECT rowid FROM {table_name} LIMIT 1").fetchall()
        return f"SELECT chunk_id, file_name, file_path, body, metadata FROM {table_name} ORDER BY rowid DESC LIMIT {limit}"
    except sqlite3.OperationalError:
        pass
    return f"SELECT chunk_id, file_name, file_path, body, metadata FROM {table_name} LIMIT {limit}"


def _parse_args() -> argparse.Namespace:
    """커맨드 라인 인자를 파싱한다."""

    parser = argparse.ArgumentParser(
        description="SQLite 테이블 데이터를 빠르게 확인한다."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="조회할 최대 레코드 수 (기본값: 200)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    db_path = Path("data/db/playground.sqlite")
    # 예시: 일반 테이블은 rag_chunks, 벡터 가상 테이블은 vec_rag_chunks_emb_body
    rows = quick_view(db_path, "rag_chunks", limit=args.limit)
    print(json.dumps(rows, ensure_ascii=False, indent=2))
