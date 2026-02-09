"""
목적: Chat 기본 시스템 프롬프트를 정의한다.
설명: textwrap + PromptTemplate 기반 모듈 싱글턴 프롬프트를 제공한다.
디자인 패턴: 모듈 싱글턴
참조: src/base_template/core/chat/nodes/reply_node.py
"""

from __future__ import annotations

import textwrap

from langchain_core.prompts import PromptTemplate

_SYSTEM_PROMPT = textwrap.dedent(
"""
You are an helpful Assistant.

<Requirements>
- Always answer in Korean.  
</Requirements>
"""
).strip()

SYSTEM_PROMPT = PromptTemplate.from_template(_SYSTEM_PROMPT)
