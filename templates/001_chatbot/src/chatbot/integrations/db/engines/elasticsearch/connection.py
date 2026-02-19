"""
목적: Elasticsearch 연결 관리 모듈을 제공한다.
설명: 클라이언트 생성/종료와 옵션 클라이언트 반환을 담당한다.
디자인 패턴: 매니저 패턴
참조: src/chatbot/integrations/db/engines/elasticsearch/engine.py
"""

from __future__ import annotations

from typing import Optional

from chatbot.shared.logging import Logger


class ElasticConnectionManager:
    """Elasticsearch 연결 관리자."""

    def __init__(
        self,
        hosts: list[str],
        logger: Logger,
        elasticsearch_cls,
        ca_certs: Optional[str],
        verify_certs: Optional[bool],
        ssl_assert_fingerprint: Optional[str],
    ) -> None:
        self._hosts = hosts
        self._logger = logger
        self._elasticsearch_cls = elasticsearch_cls
        self._ca_certs = ca_certs
        self._verify_certs = verify_certs
        self._ssl_assert_fingerprint = ssl_assert_fingerprint
        self._client: Optional[object] = None

    def connect(self) -> None:
        """Elasticsearch 연결을 초기화한다."""

        if self._elasticsearch_cls is None:
            raise RuntimeError("elasticsearch 패키지가 설치되어 있지 않습니다.")
        if self._client is not None:
            return
        options: dict = {}
        if self._ca_certs:
            options["ca_certs"] = self._ca_certs
        if self._verify_certs is not None:
            options["verify_certs"] = self._verify_certs
        if self._ssl_assert_fingerprint:
            options["ssl_assert_fingerprint"] = self._ssl_assert_fingerprint
        self._client = self._elasticsearch_cls(self._hosts, **options)
        self._logger.info("Elasticsearch 연결이 초기화되었습니다.")

    def close(self) -> None:
        """Elasticsearch 연결을 종료한다."""

        if self._client is None:
            return
        self._client.close()
        self._client = None
        self._logger.info("Elasticsearch 연결이 종료되었습니다.")

    def ensure_client(self):
        """초기화된 Elasticsearch 클라이언트를 반환한다."""

        if self._client is None:
            raise RuntimeError("Elasticsearch 연결이 초기화되지 않았습니다.")
        return self._client

    def with_options(self, ignore_status: int | list[int] | None):
        """옵션 클라이언트를 반환한다."""

        client = self.ensure_client()
        if ignore_status is None:
            return client
        return client.options(ignore_status=ignore_status)
