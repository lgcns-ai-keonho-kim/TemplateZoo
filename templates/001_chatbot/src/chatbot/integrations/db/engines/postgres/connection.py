"""
목적: PostgreSQL 연결 관리 모듈을 제공한다.
설명: 연결 초기화/종료와 PGVector 타입 등록을 담당한다.
디자인 패턴: 매니저 패턴
참조: src/chatbot/integrations/db/engines/postgres/engine.py
"""

from __future__ import annotations

from typing import Optional

from chatbot.shared.logging import Logger
from chatbot.integrations.db.engines.postgres.vector_adapter import (
    PostgresVectorAdapter,
)


class PostgresConnectionManager:
    """PostgreSQL 연결 관리자."""

    def __init__(
        self,
        dsn: str,
        logger: Logger,
        psycopg2_module,
        vector_adapter: PostgresVectorAdapter,
    ) -> None:
        self._dsn = dsn
        self._logger = logger
        self._psycopg2 = psycopg2_module
        self._vector_adapter = vector_adapter
        self._connection: Optional[object] = None

    def connect(self) -> None:
        """PostgreSQL 연결을 초기화한다."""

        if self._psycopg2 is None:
            raise RuntimeError("psycopg2-binary 패키지가 설치되어 있지 않습니다.")
        if self._connection is not None:
            return
        self._connection = self._psycopg2.connect(self._dsn)
        self._vector_adapter.register(self._connection)
        self._logger.info("PostgreSQL 연결이 초기화되었습니다.")

    def close(self) -> None:
        """PostgreSQL 연결을 종료한다."""

        if self._connection is None:
            return
        self._connection.close()
        self._connection = None
        self._logger.info("PostgreSQL 연결이 종료되었습니다.")

    def ensure_connection(self):
        """초기화된 PostgreSQL 연결 객체를 반환한다."""

        if self._connection is None:
            raise RuntimeError("PostgreSQL 연결이 초기화되지 않았습니다.")
        return self._connection
