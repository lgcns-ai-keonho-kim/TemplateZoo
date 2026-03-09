"""
목적: Text-to-SQL 조회 대상 DB 레지스트리를 제공한다.
설명: target alias별 DBClient를 등록/해석하고 종료 시 일괄 close를 지원한다.
디자인 패턴: 레지스트리 패턴
참조: src/text_to_sql/api/chat/services/runtime.py, src/text_to_sql/shared/chat/nodes/raw_sql_executor.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from text_to_sql.integrations.db.client import DBClient
from text_to_sql.shared.exceptions import BaseAppException, ExceptionDetail


@dataclass(frozen=True)
class QueryTarget:
    """조회 대상 DB 엔트리."""

    alias: str
    client: DBClient
    engine: str


class QueryTargetRegistry:
    """target alias -> DBClient 레지스트리."""

    def __init__(self) -> None:
        self._targets: Dict[str, QueryTarget] = {}
        self._default_alias: str = ""

    @property
    def default_alias(self) -> str:
        """기본 target alias를 반환한다."""

        return self._default_alias

    def register(
        self,
        *,
        alias: str,
        client: DBClient,
        engine: str,
        is_default: bool = False,
    ) -> None:
        """target 엔트리를 등록한다."""

        normalized_alias = str(alias).strip()
        normalized_engine = str(engine).strip().lower()
        if not normalized_alias:
            detail = ExceptionDetail(
                code="QUERY_TARGET_ALIAS_EMPTY",
                cause="alias 값이 비어 있습니다.",
            )
            raise BaseAppException("조회 대상 alias가 비어 있습니다.", detail)
        if normalized_alias in self._targets:
            detail = ExceptionDetail(
                code="QUERY_TARGET_DUPLICATED",
                cause=f"alias={normalized_alias}",
            )
            raise BaseAppException("조회 대상 alias가 중복되었습니다.", detail)

        self._targets[normalized_alias] = QueryTarget(
            alias=normalized_alias,
            client=client,
            engine=normalized_engine,
        )
        if is_default or not self._default_alias:
            self._default_alias = normalized_alias

    def resolve(self, alias: str | None = None) -> QueryTarget:
        """alias 기반 target을 해석한다."""

        normalized_alias = str(alias or "").strip()
        if normalized_alias:
            target = self._targets.get(normalized_alias)
            if target is None:
                detail = ExceptionDetail(
                    code="QUERY_TARGET_NOT_FOUND",
                    cause=f"alias={normalized_alias}",
                )
                raise BaseAppException("조회 대상 alias를 찾을 수 없습니다.", detail)
            return target

        if self._default_alias:
            return self._targets[self._default_alias]

        detail = ExceptionDetail(
            code="QUERY_TARGET_EMPTY",
            cause="등록된 query target이 없습니다.",
        )
        raise BaseAppException("조회 대상이 초기화되지 않았습니다.", detail)

    def aliases(self) -> list[str]:
        """등록된 alias 목록을 반환한다."""

        return sorted(self._targets.keys())

    def get(self, alias: str) -> Optional[QueryTarget]:
        """alias 엔트리를 조회한다."""

        return self._targets.get(str(alias).strip())

    def close_all(self) -> None:
        """등록된 모든 DBClient를 종료한다."""

        for alias in self.aliases():
            target = self._targets.get(alias)
            if target is None:
                continue
            target.client.close()


__all__ = ["QueryTarget", "QueryTargetRegistry"]
