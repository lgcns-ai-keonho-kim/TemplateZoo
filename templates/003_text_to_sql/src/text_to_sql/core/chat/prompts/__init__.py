"""
목적: Chat 프롬프트 공개 API를 제공한다.
설명: 답변, 안전성, 컨텍스트 전략, 스키마 선택, raw SQL 생성 프롬프트를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/text_to_sql/core/chat/prompts/chat_prompt.py
"""

from text_to_sql.core.chat.prompts.chat_prompt import CHAT_PROMPT
from text_to_sql.core.chat.prompts.context_strategy_prompt import (
    CONTEXT_STRATEGY_PROMPT,
)
from text_to_sql.core.chat.prompts.raw_sql_generation_prompt import (
    RAW_SQL_GENERATION_PROMPT,
)
from text_to_sql.core.chat.prompts.safeguard_prompt import SAFEGUARD_PROMPT
from text_to_sql.core.chat.prompts.schema_selection_prompt import (
    SCHEMA_SELECTION_PROMPT,
)

__all__ = [
    "SAFEGUARD_PROMPT",
    "CHAT_PROMPT",
    "CONTEXT_STRATEGY_PROMPT",
    "SCHEMA_SELECTION_PROMPT",
    "RAW_SQL_GENERATION_PROMPT",
]
