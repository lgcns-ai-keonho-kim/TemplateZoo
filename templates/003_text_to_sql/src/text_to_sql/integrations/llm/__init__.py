"""
목적: LLM 통합 모듈 공개 API를 제공한다.
설명: LLM 클라이언트를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/text_to_sql/integrations/llm/client.py
"""

from text_to_sql.integrations.llm.client import LLMClient

__all__ = ["LLMClient"]
