"""
목적: DB 문서/벡터 모델 공개 API 파사드를 제공한다.
설명: 문서 및 벡터 DTO 분리 구현을 단일 진입점으로 재노출한다.
디자인 패턴: 퍼사드
참조: src/tool_proxy_agent/integrations/db/base/_vector.py, src/tool_proxy_agent/integrations/db/base/_document.py
"""

from __future__ import annotations

from tool_proxy_agent.integrations.db.base._document import Document
from tool_proxy_agent.integrations.db.base._vector import Vector

__all__ = ["Vector", "Document"]
