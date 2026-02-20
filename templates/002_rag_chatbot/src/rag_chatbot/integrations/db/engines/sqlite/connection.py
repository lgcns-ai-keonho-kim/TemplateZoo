"""
목적: SQLite 연결 관리 모듈을 제공한다.
설명: 연결 초기화/종료와 sqlite-vec 확장 로딩을 담당한다.
디자인 패턴: 매니저 패턴
참조: src/rag_chatbot/integrations/db/engines/sqlite/engine.py
"""

from __future__ import annotations

import os
import sqlite3
from typing import Optional

from rag_chatbot.shared.logging import Logger


class SqliteConnectionManager:
    """SQLite 연결 관리자."""

    def __init__(
        self,
        database_path: str,
        logger: Logger,
        enable_vector: bool,
        sqlite_vec_module,
    ) -> None:
        self._database_path = database_path
        self._logger = logger
        self._enable_vector = enable_vector
        self._sqlite_vec = sqlite_vec_module
        self._connection: Optional[sqlite3.Connection] = None
        self._supports_vector_search = enable_vector
        self._busy_timeout_ms = self._read_busy_timeout_ms()

    @property
    def supports_vector_search(self) -> bool:
        """벡터 검색 지원 여부를 반환한다."""

        return self._supports_vector_search

    def connect(self) -> None:
        """SQLite 연결을 초기화한다."""

        if self._connection is not None:
            return
        self._connection = sqlite3.connect(
            self._database_path,
            timeout=self._busy_timeout_ms / 1000.0,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._apply_pragmas()
        if self._enable_vector:
            self._load_sqlite_vec()
        self._logger.info("SQLite 연결이 초기화되었습니다.")

    def close(self) -> None:
        """SQLite 연결을 종료한다."""

        if self._connection is None:
            return
        self._connection.close()
        self._connection = None
        self._logger.info("SQLite 연결이 종료되었습니다.")

    def ensure_connection(self) -> sqlite3.Connection:
        """초기화된 SQLite 연결 객체를 반환한다."""

        if self._connection is None:
            raise RuntimeError("SQLite 연결이 초기화되지 않았습니다.")
        return self._connection

    def _load_sqlite_vec(self) -> None:
        if self._sqlite_vec is None:
            self._supports_vector_search = False
            raise RuntimeError("sqlite-vec 패키지가 설치되어 있지 않습니다.")
        connection = self.ensure_connection()
        connection.enable_load_extension(True)
        self._sqlite_vec.load(connection)
        connection.enable_load_extension(False)

    def _apply_pragmas(self) -> None:
        """동시성 친화 SQLite PRAGMA를 적용한다."""

        connection = self.ensure_connection()
        connection.execute(f"PRAGMA busy_timeout={self._busy_timeout_ms}")
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
        except sqlite3.DatabaseError as error:
            self._logger.warning(f"SQLite PRAGMA 적용 경고: {error}")

    def _read_busy_timeout_ms(self) -> int:
        raw = os.getenv("SQLITE_BUSY_TIMEOUT_MS", "5000")
        try:
            value = int(raw)
        except ValueError:
            return 5000
        return max(0, value)
