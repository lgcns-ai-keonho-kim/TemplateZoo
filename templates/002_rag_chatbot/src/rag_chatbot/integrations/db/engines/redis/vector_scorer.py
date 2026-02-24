"""
목적: Redis 벡터 유사도 계산기를 제공한다.
설명: 코사인 유사도 기반 점수를 계산한다.
디자인 패턴: 유틸리티 클래스
참조: src/rag_chatbot/integrations/db/engines/redis/engine.py
"""

from __future__ import annotations

import math
from typing import List


class RedisVectorScorer:
    """코사인 유사도 계산기."""

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """두 벡터의 코사인 유사도를 계산한다."""

        if len(a) != len(b):
            return float("-inf")
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return float("-inf")
        return dot / (norm_a * norm_b)
