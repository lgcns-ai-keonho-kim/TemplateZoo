"""
목적: Chat 기본 시스템 프롬프트를 정의한다.
설명: textwrap + PromptTemplate 기반 모듈 싱글턴 프롬프트를 제공한다.
디자인 패턴: 모듈 싱글턴
참조: src/base_template/core/chat/nodes/response_node.py
"""

from __future__ import annotations

import textwrap

from langchain_core.prompts import PromptTemplate

_CHAT_PROMPT = textwrap.dedent(
"""
You are an helpful Assistant.

<Requirements>
- Always answer in Korean.  
</Requirements>

<Context>
- latest_user_query: {user_message}
</Context>
"""
).strip()

CHAT_PROMPT = PromptTemplate.from_template(_CHAT_PROMPT)
