"""
목적: Redis 연결 관리 모듈을 제공한다.
설명: 연결 초기화/종료와 클라이언트 보장을 담당한다.
디자인 패턴: 매니저 패턴
참조: src/chatbot/integrations/db/engines/redis/engine.py
"""

from __future__ import annotations

from typing import Optional

from chatbot.shared.logging import Logger


class RedisConnectionManager:
    """Redis 연결 관리자."""

    def __init__(self, url: str, logger: Logger, redis_module) -> None:
        self._url = url
        self._logger = logger
        self._redis = redis_module
        self._client: Optional[object] = None

    def connect(self) -> None:
        """Redis 연결을 초기화한다."""

        if self._redis is None:
            raise RuntimeError("redis 패키지가 설치되어 있지 않습니다.")
        if self._client is not None:
            return
        self._client = self._redis.Redis.from_url(self._url)
        self._logger.info("Redis 연결이 초기화되었습니다.")

    def close(self) -> None:
        """Redis 연결을 종료한다."""

        if self._client is None:
            return
        self._client.close()
        self._client = None
        self._logger.info("Redis 연결이 종료되었습니다.")

    def ensure_client(self):
        """초기화된 Redis 클라이언트를 반환한다."""

        if self._client is None:
            raise RuntimeError("Redis 연결이 초기화되지 않았습니다.")
        return self._client
