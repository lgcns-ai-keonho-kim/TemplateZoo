"""
목적: Chat 그래프 분기 라우트 상수를 정의한다.
설명: 현재 그래프에서 사용하는 분기 토큰만 Enum으로 관리한다.
디자인 패턴: Enum 상수 객체
참조: src/text_to_sql/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

from enum import Enum


class SafeguardRoute(str, Enum):
    """Safeguard 라우트."""

    RESPONSE = "response"
    BLOCKED = "blocked"


class MetadataRoute(str, Enum):
    """메타데이터 응답 라우트."""

    RESPONSE = "response"


SAFEGUARD_ROUTE_RESPONSE = SafeguardRoute.RESPONSE.value
SAFEGUARD_ROUTE_BLOCKED = SafeguardRoute.BLOCKED.value

METADATA_ROUTE_RESPONSE = MetadataRoute.RESPONSE.value
