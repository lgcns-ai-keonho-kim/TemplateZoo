"""
목적: MongoDB 연결 관리 모듈을 제공한다.
설명: 연결 초기화/종료와 데이터베이스 객체 보장을 담당한다.
디자인 패턴: 매니저 패턴
참조: src/chatbot/integrations/db/engines/mongodb/engine.py
"""

from __future__ import annotations

from typing import Any, Optional

from chatbot.shared.logging import Logger


class MongoConnectionManager:
    """MongoDB 연결 관리자."""

    def __init__(
        self,
        uri: str,
        database_name: str,
        auth_source: Optional[str],
        logger: Logger,
        mongo_client_cls,
    ) -> None:
        self._uri = uri
        self._database_name = database_name
        self._auth_source = auth_source
        self._logger = logger
        self._mongo_client_cls = mongo_client_cls
        self._client: Any | None = None
        self._database: Any | None = None

    def connect(self) -> None:
        """MongoDB 연결을 초기화한다."""

        if self._mongo_client_cls is None:
            raise RuntimeError("pymongo 패키지가 설치되어 있지 않습니다.")
        if self._client is not None:
            return
        if self._auth_source and "authSource=" not in self._uri:
            self._client = self._mongo_client_cls(self._uri, authSource=self._auth_source)
        else:
            self._client = self._mongo_client_cls(self._uri)
        self._database = self._client[self._database_name]
        self._logger.info("MongoDB 연결이 초기화되었습니다.")

    def close(self) -> None:
        """MongoDB 연결을 종료한다."""

        if self._client is None:
            return
        self._client.close()
        self._client = None
        self._database = None
        self._logger.info("MongoDB 연결이 종료되었습니다.")

    def ensure_database(self):
        """초기화된 MongoDB 데이터베이스 객체를 반환한다."""

        if self._database is None:
            raise RuntimeError("MongoDB 연결이 초기화되지 않았습니다.")
        return self._database
