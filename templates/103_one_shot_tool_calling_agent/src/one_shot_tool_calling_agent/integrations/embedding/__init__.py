"""
목적: 임베딩 통합 모듈 공개 API를 제공한다.
설명: 임베딩 클라이언트를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/one_shot_tool_calling_agent/integrations/embedding/client.py
"""

from one_shot_tool_calling_agent.integrations.embedding.client import EmbeddingClient

__all__ = ["EmbeddingClient"]
